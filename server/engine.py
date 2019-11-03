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
                 players=[{'name': 'User0', 'token': 'token1'}], max_processes=10, max_staging_size=50):
        self.__socketio = socketio
        self.seconds_per_tick = seconds_per_tick
        self.staging_file = staging_file
        self.ticks_per_round = ticks_per_round
        self.load_interval = load_interval
        self.players = {}
        self.staged_payloads = {}
        self.max_staging_size = max_staging_size
        for idx, player in enumerate(players):
            self.players[idx] = corewar.players.Player(player['name'], idx, player['token'])

        self.mars = corewar.mars.MARS(corewar.core.Core(size=core_size, \
            core_event_recorder=self.core_event_handler), players=self.players, \
            max_processes=max_processes, seconds_per_tick=self.seconds_per_tick, \
            runtime_event_handler=self.runtime_event_handler)
        
    def core_event_handler(self, events):
        self.__socketio.emit('core_state', events)
        
    def runtime_event_handler(self, events):
        self.__socketio.emit('events', events)

    def save_payload_to_disk(self, payload):
        with open("history.txt", "a+") as w:
            w.write("%s (%s): [%s]\n" % (self.players[payload[0]], self.mars.tick_count, ":::".join(payload[1])))

    def load_staged_program(self, player_id):
        """
        Read staged data for the player_id
        from the staging file and insert those
        bytes into a random location in the cores memory
        """
        if player_id not in self.staged_payloads.keys() or self.staged_payloads[player_id] == []:
            print "nothing staged for player %s" % self.players[player_id]
            return
        
        assembled_instructions = corewar.yeetcode.assemble(self.staged_payloads[player_id][1])
        load_idx = random.randint(0, self.mars.core.size/self.load_interval) * self.load_interval

        self.mars.core[load_idx] = assembled_instructions
        new_thread = corewar.players.Thread(pc=load_idx, owner=player_id)
        self.mars.spawn_new_thread(new_thread)
        
        if len(self.mars.players[player_id].threads) > self.mars.max_processes:
            self.mars.kill_oldest_thread(player_id)
        
        self.save_payload_to_disk(self.staged_payloads[player_id])
        self.staged_payloads[player_id] = []

    def run(self):
        """
        Main game loop
        Start loading staged data after 1 round
        Do 1 tick then sleep for the amount of seconds
        specified in the seconds_per_tick variable
        """
        while True:
            #TODO: allow for more players than ticks_per_round
            target_player = self.mars.tick_count % self.ticks_per_round
            if target_player in self.players:
                print 'Loading staged data for player {}'.format(self.players[target_player])
                self.load_staged_program(target_player)
            self.mars.tick()
            for thread in self.mars.thread_pool: print thread