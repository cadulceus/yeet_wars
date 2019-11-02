from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
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
    
e = engine.Engine(socketio=socketio, **config)
if not os.path.isfile(e.staging_file):
    with open(e.staging_file, 'w') as w:
        w.write('{}')
engine_thread = threading.Thread(target=e.run)
engine_thread.daemon = True
engine_thread.start()

@app.route('/state')
def get_state():
    """
    GET /state
    Returns the current bytearray of the yeetcode game core
    """
    return jsonify(list(e.mars.core.bytes))

@app.route('/stage', methods=['POST'])
def stage_program():
    """
    POST /stage
    Expects a POST with JSON containing a player ID
    and the yeetcode assembly instructions to stage for that player
    Example:
    $ curl -H 'content-type: application/json' -d '{"player_id": 0, "instructions": "YEET #0, #4"}' 
    -XPOST localhost:5000/stage
    {"status":"success"} 
    """
    if 'player_id' not in request.json:
        return jsonify({'error': 'player_id arg required'})
    if 'instructions' not in request.json:
        return jsonify({'error': 'instructions arg required'})

    player_id = str(request.json['player_id'])
    instructions = str(request.json['instructions']).split('\n')
    if len(instructions) > e.max_staging_size:
        instructions = instructions[:e.max_staging_size]
    e.staged_payloads[int(player_id)] = [int(player_id), instructions]
    return jsonify({'status': 'success'})
  
@socketio.on('connect')
def connected_client():
  emit('connection', list(e.mars.core.bytes))


if __name__ == '__main__':
  socketio.run(app, host='0.0.0.0', debug=False)