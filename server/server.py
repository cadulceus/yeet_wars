from flask import Flask, jsonify, request
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
        env_vars['seconds_per_tick'] = int(seconds_per_tick)
    
    ticks_per_round = os.getenv('YEET_TICKS_PER_ROUND')
    if ticks_per_round:
        env_vars['ticks_per_round'] = int(ticks_per_round)
    
    nplayers = os.getenv('YEET_NPLAYERS')
    if nplayers:
        env_vars['nplayers'] = int(nplayers)

    staging_file = os.getenv('YEET_STAGING_FILE')
    if staging_file:
        env_vars['staging_file'] = staging_file

    core_size = os.getenv('YEET_CORE_SIZE')
    if core_size:
        env_vars['core_size'] = int(core_size)
        
    return env_vars

env_vars = load_env_vars()
e = engine.Engine(**env_vars)
if not os.path.isfile(e.staging_file):
    with open(e.staging_file, 'w') as w:
        w.write('{}')
engine_thread = threading.Thread(target=e.run)
engine_thread.daemon = True
engine_thread.start()

app = Flask(__name__)

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
    $ curl -H 'content-type: application/json' -d '{"player_id": 0, "instructions": "YEET 1, 1"}' 
    -XPOST localhost:5000/stage
    {"status":"success"} 
    """
    if 'player_id' not in request.json:
        return jsonify({'error': 'player_id arg required'})
    if 'instructions' not in request.json:
        return jsonify({'error': 'instructions arg required'})

    player_id = str(request.json['player_id'])
    instructions = str(request.json['instructions']).split('\n')
    parsed_instructions = corewar.yeetcode.parse(instructions)
    program_bytes = []
    for instruction in parsed_instructions:
        program_bytes += instruction.mcode
    with open(e.staging_file, 'r') as r:
        staging_data = json.load(r)

    staging_data[player_id] = program_bytes
    with open(e.staging_file, 'w') as w:
        json.dump(staging_data, w)
    return jsonify({'status': 'success'})

app.run(host='0.0.0.0', debug=False)