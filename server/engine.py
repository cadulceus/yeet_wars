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
    def __init__(self, seconds_per_tick=10, nplayers=2,
                 staging_file='staging.json', ticks_per_round=20):
        self.seconds_per_tick = seconds_per_tick
        self.players = [i for i in range(nplayers)]
        self.staging_file = staging_file
        self.ticks_per_round = ticks_per_round

        self.mars = corewar.mars.MARS()

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
        load_idx = random.randint(0, self.mars.core.size - 1)

        self.mars.core[load_idx] = program_bytes
        new_thread = corewar.players.Thread(pc=load_idx, owner=player_id)
        self.mars.next_tick_pool.append(new_thread)

    def run(self):
        """
        Main game loop
        Start loading staged data after 1 round
        Do 1 tick then sleep for the amount of seconds
        specified in the seconds_per_tick variable
        """
        while True:
            if self.mars.tick_count >= self.ticks_per_round:
                target_player = self.mars.tick_count % self.ticks_per_round
                if target_player in self.players:
                    print 'Loading staged data for player {}'.format(target_player)
                    self.load_staged_program(target_player)
            self.mars.tick()
            time.sleep(self.seconds_per_tick)