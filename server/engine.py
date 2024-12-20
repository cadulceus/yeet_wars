import corewar.core
import corewar.mars
import corewar.players
import random
import time
import copy

class Engine(object):
    """Game engine
    Keeps track of players, executes core ticks,
    saves data to database for web API, loads staging
    data from the database.
    """
    def __init__(self, socketio=None, seconds_per_tick=10,
                 staging_file='staging.json', ticks_per_stage=1,
                 core_size=8192, load_interval=200,
                 players=[{'name': 'User0', 'token': 'token1'}], max_processes=10, max_staging_size=50, batch_events=True):
        self.__socketio = socketio
        self.seconds_per_tick = seconds_per_tick
        self.staging_file = staging_file
        self.ticks_per_stage = ticks_per_stage
        self.load_interval = load_interval
        self.players = {}
        self.staged_payloads = {}
        self.max_staging_size = max_staging_size
        self.used_colors = []
        self.batch_events= batch_events
        self.core_event_cache = []
        self.update_thread_event_cache = []
        self.kill_thread_event_cache = []
        for i in range(len(players)):
            self.used_colors.append(self.generate_new_color(self.used_colors))
        for idx, player in enumerate(players):
            self.players[idx] = corewar.players.Player(player['name'], idx, player['token'], color=self.used_colors[idx])

        self.mars = corewar.mars.MARS(corewar.core.Core(size=core_size, \
            core_event_recorder=self.core_event_handler), players=self.players, \
            max_processes=max_processes, seconds_per_tick=self.seconds_per_tick, \
            runtime_event_handler=self.runtime_event_handler, update_thread_event_handler=self.update_thread_event_handler, \
            kill_thread_event_handler=self.kill_thread_event_handler, ticket_event_handler=self.tick_event_handler)
        
        if batch_events:
            self.cached_core_bytes = copy.deepcopy(self.mars.core.bytes)
        else:
            self.cached_core_bytes = self.mars.core.bytes
  
    # TODO: these color functions should really be broken out 
    # code for color generation taken from https://gist.github.com/adewes/5884820 
    def get_random_color(self, pastel_factor = 0.5):
        return [(x+pastel_factor)/(1.0+pastel_factor) for x in [random.uniform(0,1.0) for i in [1,2,3]]]

    def color_distance(self, c1,c2):
        return sum([abs(x[0]-x[1]) for x in zip(c1,c2)])

    def generate_new_color(self, existing_colors,pastel_factor = 0.5):
        max_distance = None
        best_color = None
        for i in range(0,100):
            color = self.get_random_color(pastel_factor = pastel_factor)
            if not existing_colors:
                return color
            best_distance = min([self.color_distance(color,c) for c in existing_colors])
            if not max_distance or best_distance > max_distance:
                max_distance = best_distance
                best_color = color
        return best_color
    
    def float_to_hex_colors(self, color) -> list[str]:
        hexified_colors = [hex(int(255 * percentage))[2:] for percentage in color]
        return "#" + "".join(hexified_colors)

    def add_player(self, player_name, player_id, player_token):
        if player_id in self.players:
            return False
        new_color = self.generate_new_color(self.used_colors)
        self.players[player_id] = corewar.players.Player(player_name, player_id, player_token, color=new_color)
        self.used_colors.append(new_color)
        return True
    
    def emit_core_update(self, events: list[list[int]]):
        if events:
            self.__socketio.emit('core_state', events, room='player')
    
    def emit_thread_update(self, events: list[tuple[int, int, list[str]]]):
        if events:
            self.__socketio.emit('update_thread', events, room='player')
    
    def emit_thread_kill(self, events: list[int]):
        self.__socketio.emit('kill_thread', events, room='player')
        
    def core_event_handler(self, events: list[list[int]]):
        if self.batch_events:
            self.core_event_cache += events
        else:
            self.emit_core_update(events)
        
    def update_thread_event_handler(self, pid, pc, color):
        if self.batch_events:
            self.update_thread_event_cache.append((pid, pc, self.float_to_hex_colors(color)))
        else:
            self.emit_thread_update([(pid, pc, self.float_to_hex_colors(color))])
        
    def kill_thread_event_handler(self, events):
        if self.batch_events:
            self.kill_thread_event_cache.append(events)
        else:
            self.emit_thread_kill(events)

    def tick_event_handler(self):
        if self.batch_events:
            # when events are batched, the /state endpoint must return a snapshot of the core rather than the live core to avoid desyncronization
            self.cached_core_bytes = copy.deepcopy(self.mars.core.bytes)

            self.emit_core_update(self.core_event_cache)
            self.emit_thread_kill(self.kill_thread_event_cache)
            self.emit_thread_update(self.update_thread_event_cache)
            self.core_event_cache = []
            self.kill_thread_event_cache = []
            self.update_thread_event_cache = []
        
    def runtime_event_handler(self, events):
        self.__socketio.emit('events', "Cycle number: %s\n%s\n\n%s" % (self.mars.tick_count, events, time.ctime(time.time())), room='player')

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
            return
        
        try:
            assembled_instructions = corewar.yeetcode.assemble(self.staged_payloads[player_id][1])
        except Exception as e:
            self.runtime_event_handler("Failed to assemble payload. \
                Staging endpoint expects a string of newline separated instructions: %s" % e)
            self.staged_payloads[player_id] = []
            return
            
        load_idx = random.randint(0, self.mars.core.size//self.load_interval) * self.load_interval

        self.mars.core[load_idx] = assembled_instructions
        new_thread = corewar.players.Thread(pc=load_idx, owner=player_id)
        self.mars.spawn_new_thread(new_thread)
        
        if len(self.mars.players[player_id].threads) > self.mars.max_processes:
            self.mars.kill_oldest_thread(player_id)
        
        self.runtime_event_handler("Loading new thread for %s at pc %i: \n$ %s" % \
            (self.players[player_id].name, load_idx, "\n$ ".join(self.staged_payloads[player_id][1])))
        
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
            # if its a staging round, stage a program from a player sequentially
            if self.mars.tick_count % self.ticks_per_stage == 0:
                target_player = (self.mars.tick_count // self.ticks_per_stage) % len(self.players)
                if target_player in self.players:
                    self.load_staged_program(target_player)

            self.mars.tick()
            current_scores = []
            for player in self.players:
                current_scores.append(["%s: %s" % (str(self.players[player]), self.players[player].score), \
                    self.float_to_hex_colors(self.players[player].color)])
            # Shitty hack to show the current tick count
            current_scores.append(["Current tick count: %s" % self.mars.tick_count, "#FFFFFF"])
            self.__socketio.emit('player_scores', (current_scores, 'player'))
            for thread in self.mars.thread_pool: print(thread)
            print("\n==========================\n")