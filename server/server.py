from flask import Flask, abort, jsonify, request
from flask_socketio import SocketIO, emit
from functools import wraps
import corewar.yeetcode
import engine
import json
import os
import threading

def load_env_vars():
    """
    Load the yeetcode engine variables from environment variables
    """
    env_vars = {}
    seconds_per_tick = os.getenv('YEET_SECONDS_PER_TICK')
    if seconds_per_tick:
        env_vars['seconds_per_tick'] = float(seconds_per_tick)
    
    ticks_per_round = os.getenv('YEET_TICKS_PER_ROUND')
    if ticks_per_round:
        env_vars['ticks_per_round'] = int(ticks_per_round)

    staging_file = os.getenv('YEET_STAGING_FILE')
    if staging_file:
        env_vars['staging_file'] = staging_file

    core_size = os.getenv('YEET_CORE_SIZE')
    if core_size:
        env_vars['core_size'] = int(core_size)
    
    max_processes = os.getenv('YEET_MAX_PROCESSES')
    if max_processes:
        env_vars['config_file'] = max_processes
        
    return env_vars

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'keyboard cat')
socketio = SocketIO(app, cors_allowed_origins="*")

config_file = os.getenv('YEET_CONFIG_FILE')

env_vars = load_env_vars()
if config_file and os.path.isfile(config_file):
    with open(config_file, "r") as r:
        config = json.load(r)
        print config
else:
    config = env_vars

app.config['ADMIN_TOKEN'] = config.pop('admin_token').lower()
app.config['PLAYER_TOKENS'] = {}
if 'players' in config:
    for i, entry in enumerate(config['players']):
        player_name = entry['name']
        player_token = entry['token']
        app.config['PLAYER_TOKENS'][player_token] = {'name': player_name, 'id': i}

def admin_authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'Authorization' in request.headers:
            abort(401)

        data = request.headers['Authorization'].encode('ascii', 'ignore')
        token = data.lower().replace('bearer: ', '')
        if token != app.config['ADMIN_TOKEN']:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def player_authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'Authorization' in request.headers:
            abort(401)

        data = request.headers['Authorization'].encode('ascii', 'ignore')
        token = data.lower().replace('bearer: ', '')
        if token not in app.config['PLAYER_TOKENS']:
            abort(401)
        player = app.config['PLAYER_TOKENS'][token]
        return f(player, *args, **kwargs)
    return decorated_function
    
e = engine.Engine(socketio=socketio, **config)
if not os.path.isfile(e.staging_file):
    with open(e.staging_file, 'w') as w:
        w.write('{}')
engine_thread = threading.Thread(target=e.run)
engine_thread.daemon = True
engine_thread.start()

@app.route('/state')
@admin_authorize
def get_state():
    """
    GET /state
    Returns the current bytearray of the yeetcode game core
    """
    return jsonify(list(e.mars.core.bytes))

@app.route('/add_player', methods=['POST'])
@admin_authorize
def add_player():
    """
    POST /add_player
    Adds a player to the game
    Example:
    $ curl \
        -H 'content-type: application/json' \
        -H 'Authorization: Bearer admintokenyeet' \
        -d '{"name": "newplayer", "token": "newtoken"}' \
        -XPOST localhost:5000/add_player
    {'status': 'success'}
    """
    if not request.json:
        return jsonify({'status': 'error', 'message': 'no data posted'})
    
    if 'name' not in request.json or 'token' not in request.json:
        return jsonify({'status': 'error', 'message': 'name and token fields required'})

    player_name = request.json['name']
    player_token = request.json['token']

    if player_token in app.config['PLAYER_TOKENS']:
        return jsonify({'status': 'error', 'message': 'token already in use'})

    app.config['PLAYER_TOKENS'][player_token] = {'name': player_name, 'id': len(app.config['PLAYER_TOKENS'])}
    error = not e.add_player(player_name, app.config['PLAYER_TOKENS'][player_token]['id'], player_token)
    print e.players
    if error:
        return jsonify({'status': 'error', 'message': 'failed to add player to engine'})
    
    return jsonify({'status': 'success'})

@app.route('/stage', methods=['POST'])
@player_authorize
def stage_program(player):
    """
    POST /stage
    Expects a POST with JSON containing a player ID
    and the yeetcode assembly instructions to stage for that player
    Example:
    $ curl \
        -H 'content-type: application/json' \
        -H 'Authorization: Bearer: token1' \
        -d '{"instructions": "YEET #0, #4"}' \
        -XPOST localhost:5000/stage
    {"status":"success"} 
    """
    if not request.json:
        return jsonify({'error': 'no content'})
    if 'instructions' not in request.json:
        return jsonify({'error': 'instructions arg required'})

    player_id = player['id']
    instructions = str(request.json['instructions']).split('\n')
    if len(instructions) > e.max_staging_size:
        instructions = instructions[:e.max_staging_size]
    e.staged_payloads[player_id] = [player_id, instructions]
    return jsonify({'status': 'success'})
  
@socketio.on('connect')
@admin_authorize
def connected_client():
  emit('core_connection', list(e.mars.core.bytes))
  emit('event_connection', "Events feed loaded")


if __name__ == '__main__':
  socketio.run(app, host='0.0.0.0', debug=False)