import corewar.core
import corewar.mars
import corewar.players
import json
import random
import time

class Engine(object):
    """Game engine
    Keeps track of players, executes core ticks,
    saves data to database for web API, loads staging
    data from the database.
    """
    def __init__(self, socketio=None, seconds_per_tick=10, nplayers=2,
                 staging_file='staging.json', ticks_per_round=20,
                 core_size=8192, load_interval=200):
        self.__socketio = socketio
        self.seconds_per_tick = seconds_per_tick
        self.players = [i for i in range(nplayers)]
        self.staging_file = staging_file
        self.ticks_per_round = ticks_per_round
        self.load_interval = load_interval

        self.mars = corewar.mars.MARS(corewar.core.Core(size=core_size))

    def load_staged_program(self, player_id):
        """
        Read staged data for the player_id
        from the staging file and insert those
        bytes into a random location in the cores memory
        """
        try:
            with open(self.staging_file, 'r') as r:
                staging_data = json.load(r)
        except Exception as e:
            print 'Could not read {}: {}'.format(self.staging_file, e)
            return

        player_key = str(player_id)
        if player_key not in staging_data:
            return
        
        program_bytes = staging_data[player_key]
        load_idx = random.randint(0, self.mars.core.size/self.load_interval) * self.load_interval

        self.mars.core[load_idx] = program_bytes
        new_thread = corewar.players.Thread(pc=load_idx, owner=player_id)
        self.mars.spawn_new_thread(new_thread)

    def run(self):
        """
        Main game loop
        Start loading staged data after 1 round
        Do 1 tick then sleep for the amount of seconds
        specified in the seconds_per_tick variable
        """
        while True:
            #for thread in self.mars.next_tick_pool: print thread
            target_player = self.mars.tick_count % self.ticks_per_round
            if target_player in self.players:
                print 'Loading staged data for player {}'.format(target_player)
                self.load_staged_program(target_player)
            self.mars.tick()
            for thread in self.mars.thread_pool: print thread
            # TODO: maybe make this slightly more network efficient (or be even more real-time)
            if self.__socketio is not None: # broadcast state every tick.
              self.__socketio.emit('state', list(self.mars.core.bytes))
            time.sleep(self.seconds_per_tick)