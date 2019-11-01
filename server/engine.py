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
    def __init__(self, socketio=None, seconds_per_tick=10,
                 staging_file='staging.json', ticks_per_round=20,
                 core_size=8192, load_interval=200,
                 players={"0": "User0"}, max_processes=10):
        self.__socketio = socketio
        self.seconds_per_tick = seconds_per_tick
        self.staging_file = staging_file
        self.ticks_per_round = ticks_per_round
        self.load_interval = load_interval
        self.players = {}
        for idx, player in enumerate(players):
            self.players[int(idx)] = corewar.players.Player(player, int(idx), players[player])

        self.mars = corewar.mars.MARS(corewar.core.Core(size=core_size, \
            event_recorder=self.core_event_handler), players=self.players, \
            max_processes=max_processes, seconds_per_tick=self.seconds_per_tick)
        
    def core_event_handler(self, events):
        self.__socketio.emit('core_state', events)

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
        if len(self.mars.players[player_id].threads) > self.mars.max_processes:
            self.mars.kill_oldest_thread(player_id)

    def run(self):
        """
        Main game loop
        Start loading staged data after 1 round
        Do 1 tick then sleep for the amount of seconds
        specified in the seconds_per_tick variable
        """
        while True:
            target_player = self.mars.tick_count % self.ticks_per_round
            if target_player in self.players:
                print 'Loading staged data for player {}'.format(self.players[target_player])
                self.load_staged_program(target_player)
            self.mars.tick()
            for thread in self.mars.thread_pool: print thread