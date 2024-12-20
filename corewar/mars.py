#! /usr/bin/env python
# coding: utf-8

from copy import copy, deepcopy
from random import randint, shuffle, choice
import operator, struct

from binascii import hexlify
from .core import Core
from time import sleep
from .yeetcode import *
from .players import *

__all__ = ['MARS', 'EVENT_EXECUTED', 'EVENT_I_WRITE', 'EVENT_I_READ',
           'EVENT_A_DEC', 'EVENT_A_INC', 'EVENT_B_DEC', 'EVENT_B_INC',
           'EVENT_A_READ', 'EVENT_A_WRITE', 'EVENT_B_READ', 'EVENT_B_WRITE',
           'EVENT_A_ARITH', 'EVENT_B_ARITH']

# Event types
EVENT_EXECUTED = 0
EVENT_I_WRITE  = 1
EVENT_I_READ   = 2
EVENT_A_DEC    = 3
EVENT_A_INC    = 4
EVENT_B_DEC    = 5
EVENT_B_INC    = 6
EVENT_A_READ   = 7
EVENT_A_WRITE  = 8
EVENT_B_READ   = 9
EVENT_B_WRITE  = 10
EVENT_A_ARITH  = 11
EVENT_B_ARITH  = 12

class yeetTimeException(Exception):
    def __init__(self, message: str, thread: Thread, instr: Instruction):
        self.message = "Emulator Runtime Exception (%s) - thread: %s Instruction: %s" % (message, thread, instr)

    def __str__(self):
        return self.message

class MARS(object):
    """The MARS. Encapsulates a simulation.
    """

    def __init__(self, core=None, minimum_separation=100, max_processes=10, players={}, seconds_per_tick=0, \
        runtime_event_handler=lambda *args: None, update_thread_event_handler=lambda *args: None, \
        kill_thread_event_handler=lambda *args: None, ticket_event_handler=lambda *args: None):
        self.core = core if core else Core()
        self.minimum_separation = minimum_separation
        self.max_processes = max_processes if max_processes else len(self.core)
        self.thread_pool = []
        self.next_tick_pool = []
        self.tick_count = 0
        self.players = players
        self.thread_counter = 0
        self.seconds_per_tick = seconds_per_tick
        self.runtime_event_handler = runtime_event_handler
        self.update_thread_event_handler = update_thread_event_handler
        self.kill_thread_event_handler = kill_thread_event_handler
        self.tick_event_handler = ticket_event_handler

    def __iter__(self):
        return iter(self.core)

    def __len__(self):
        return len(self.core)

    def __getitem__(self, address):
        return self.core[address]
        
    def kill_thread(self, thread_id):
        for idx, thread in enumerate(self.thread_pool):
            if thread.id == thread_id:
                self.runtime_event_handler("Killing thread in thread pool %s" % thread)
                del self.thread_pool[idx]
                self.kill_thread_event_handler(thread.id)
                return
        
        for idx, thread in enumerate(self.next_tick_pool):
            if thread.id == thread_id:
                self.runtime_event_handler("Killing thread in next tick's thread pool %s" % thread)
                del self.next_tick_pool[idx]
                self.kill_thread_event_handler(thread.id)
                return
        
        raise Exception("Couldn't find player %s's oldest thread")
    
    def kill_oldest_thread(self, player_id):
        if len(self.players[player_id].threads) == 0:
            return
        self.kill_thread(self.players[player_id].threads.pop(0))

    def crash_thread(self, thread, message):
        self.kill_thread_event_handler(thread.id)
        self.runtime_event_handler("====THREAD CRASH====\n%s" % message)
        self.players[thread.owner].threads.remove(thread.id)
    
    def get_a_value(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            l_val = bytearray(instr.a_number)
        elif instr.a_mode == RELATIVE:
            l_val = self.core[instr.a_number + thread.pc : instr.a_number + thread.pc + WORD_SIZE]
        elif instr.a_mode == REGISTER_DIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                l_val = thread.xd_bytes if instr.a_number == 0 else thread.dx_bytes
            else:
                raise yeetTimeException("register a_number is not 1 or 0", thread, instr)
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                loc = struct.unpack('>I', thread.xd_bytes)[0] if instr.a_number == 0 else struct.unpack('>I', thread.dx_bytes)[0]
                l_val = self.core[loc : loc + WORD_SIZE]
            else:
                raise yeetTimeException("register a_number is not 1 or 0", thread, instr)
            
        else:
            raise yeetTimeException("a_mode is not within usable range", thread, instr)
        return l_val
                        
    def get_a_int(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            l_val = instr.a_number
        elif instr.a_mode == RELATIVE:
            l_val = struct.unpack('>I', self.core[instr.a_number + thread.pc : instr.a_number + thread.pc + WORD_SIZE])[0]
        elif instr.a_mode == REGISTER_DIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                l_val = thread.xd if instr.a_number == 0 else thread.dx
            else:
                raise yeetTimeException("register a_number is not 1 or 0", thread, instr)
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                loc = thread.xd if instr.a_number == 0 else thread.dx
                l_val = struct.unpack('>I', self.core[loc : loc + WORD_SIZE])[0]
            else:
                raise yeetTimeException("register a_number is not 1 or 0", thread, instr)
        else:
            raise yeetTimeException("a_mode is not within usable range", thread, instr)
        return l_val

    # currently unused
    def get_a_blame(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            blame = instr.owner
        elif instr.a_mode == RELATIVE:
            addr = (instr.a_number + thread.pc) % self.core.size
            possible_owners = set()
            for i in WORD_SIZE:
                possible_owners.add(self.core.owner[(addr + i) % self.core.size])
            possible_owners_count = len(possible_owners)
            if possible_owners_count > 1:
                # If there are 2 or more unique owners, return a random choice of whoever is not the thread owner
                possible_owners = filter(lambda owner: owner != thread.owner, possible_owners)
                shuffle(possible_owners)
            blame = list(possible_owners)[0]
        elif instr.a_mode == REGISTER_DIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                blame = thread.xd_blame if instr.a_number == 0 else thread.dx_blame
            else:
                raise yeetTimeException("register a_number is not 1 or 0", thread, instr)
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                addr = thread.xd if instr.a_number == 0 else thread.dx
                possible_owners = set()
                for i in WORD_SIZE:
                    possible_owners.add(self.core.owner[(addr + i) % self.core.size])
                possible_owners_count = len(possible_owners)
                if possible_owners_count > 1:
                    # If there are 2 or more unique owners, return a random choice of whoever is not the thread owner
                    possible_owners = filter(lambda owner: owner != thread.owner, possible_owners)
                    shuffle(possible_owners)
                blame = list(possible_owners)[0]
            else:
                raise yeetTimeException("register a_number is not 1 or 0", thread, instr)
        else:
            raise yeetTimeException("a_mode is not within usable range", thread, instr)
        return l_val
                        
    def get_b_value(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            r_val = struct.pack('>H', instr.b_number)
        elif instr.a_mode == RELATIVE:
            r_val = self.core[instr.b_number + thread.pc : instr.b_number + thread.pc + WORD_SIZE]
        elif instr.a_mode == REGISTER_DIRECT:
            if instr.b_number == 0 or instr.b_number == 1:
                r_val = thread.xd_bytes if instr.b_number == 0 else thread.dx_bytes
            else:
                raise yeetTimeException("register b_number is not 1 or 0", thread, instr)
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.b_number == 0 or instr.b_number == 1:
                loc = struct.unpack('>I', thread.xd_bytes)[0] if instr.b_number == 0 else struct.unpack('>I', thread.dx_bytes)[0]
                r_val = self.core[loc : loc + WORD_SIZE]
            else:
                raise yeetTimeException("register b_number is not 1 or 0", thread, instr)
        else:
            raise yeetTimeException("b_mode is not within usable range", thread, instr)
        return r_val
                        
    def get_b_int(self, instr, thread):
        if instr.b_mode == IMMEDIATE:
            r_val = instr.b_number
        elif instr.b_mode == RELATIVE:
            r_val = struct.unpack('>I', self.core[instr.b_number + thread.pc : instr.b_number + thread.pc + WORD_SIZE])[0]
        elif instr.b_mode == REGISTER_DIRECT:
            if instr.b_number == 0 or instr.b_number == 1:
                r_val = thread.xd if instr.b_number == 0 else thread.dx
            else:
                raise yeetTimeException("register b_number is not 1 or 0", thread, instr)
        elif instr.b_mode == REGISTER_INDIRECT:
            if instr.b_number == 0 or instr.b_number == 1:
                loc = thread.xd if instr.b_number == 0 else thread.dx
                r_val = struct.unpack('>I', self.core[loc : loc + WORD_SIZE])[0]
            else:
                raise yeetTimeException("register b_number is not 1 or 0", thread, instr)
        else:
            raise yeetTimeException("b_mode is not within usable range", thread, instr)
        return r_val
        
    def mov_template(self, instr, thread, op):
        """Simulate a generic move instruction
        """
        l_int = self.get_a_int(instr, thread)
        r_int = self.get_b_int(instr, thread)
        if instr.a_mode == IMMEDIATE and instr.b_mode != REGISTER_DIRECT:
            # mov with an immediate as the src is an implicit movb, with the exception of register direct
            struct_type = '>B'
            max_size = BYTE_MAX
            width = 1
            r_int = r_int >> 24
        else:
            struct_type = '>I'
            max_size = WORD_MAX
            width = 4
            
        if instr.b_mode == IMMEDIATE:
            # Move into absolute address
            derefed_immediate = struct.unpack(struct_type, self.core[instr.b_number : instr.b_number + width])[0]
            self.core[instr.b_number] = struct.pack(struct_type, op(l_int, derefed_immediate) % max_size)
            self.core.owner[instr.b_number % self.core.size] = thread.owner
        elif instr.b_mode == RELATIVE:
            # Move into a relative offset
            self.core[instr.b_number + thread.pc] = struct.pack(struct_type, op(l_int, r_int) % max_size)
            self.core.owner[(instr.b_number + thread.pc) % self.core.size] = thread.owner
        elif instr.b_mode == REGISTER_DIRECT:
            # Move into a register
            if instr.b_number == 0:
                thread.xd = struct.pack('>I', op(l_int, r_int) % max_size)
            else:
                thread.dx = struct.pack('>I', op(l_int, r_int) % max_size)
        elif instr.b_mode == REGISTER_INDIRECT:
            # Move into an absolute address held by a register
            loc = thread.xd if instr.b_number == 0 else thread.dx
            self.core[loc] = struct.pack(struct_type, op(l_int, r_int) % max_size)
            for i in range(WORD_SIZE):
                self.core.owner[(loc + i) % self.core.size] = thread.owner

    def resolve_address(self, thread, instr):
        if instr.b_mode == IMMEDIATE:
            return instr.b_number % self.core.size
        elif instr.b_mode == RELATIVE:
            return (thread.pc + instr.b_number) % self.core.size
        elif instr.b_mode == REGISTER_DIRECT:
            loc = thread.xd if instr.b_number == 0 else thread.dx
            return loc % self.core.size
        elif instr.b_mode == REGISTER_INDIRECT:
            loc = struct.unpack(">I", self.core[thread.xd : thread.xd + 4])[0] if \
                instr.b_number == 0 else \
                struct.unpack(">I", self.core[thread.dx : thread.dx + 4])[0]
            return loc % self.core.size
            
    def jmp_template(self, thread, instr):
        """Simulate a generic jump instruction
        """
        thread.pc = self.resolve_address(thread, instr)
        self.next_tick_pool.append(thread)
        self.update_thread_event_handler(thread.id, thread.pc, self.players[thread.owner].color)
    
    def yeb_template(self, thread, instr):
        """Simulate a generic xchg instruction
        """
        l_val = self.get_a_int(instr, thread)
        r_val = self.get_b_int(instr, thread)

        # Resolve A value based on mode
        if instr.a_mode == IMMEDIATE:
            deref_lval = self.core[l_val : l_val + 4]
        elif instr.a_mode == RELATIVE:
            deref_lval = struct.pack(">I", l_val)
        elif instr.a_mode == REGISTER_DIRECT:
            deref_lval = struct.pack(">I", thread.xd) if instr.a_number == XD_REGISTER else \
                struct.pack(">I", thread.dx)
        else:
            deref_lval = struct.pack(">I", l_val)

        # Resolve B value based on mode
        if instr.b_mode == IMMEDIATE:
            deref_rval = self.core[r_val : r_val + 4]
        elif instr.b_mode == RELATIVE:
            deref_rval = struct.pack(">I", r_val)
        elif instr.b_mode == REGISTER_DIRECT:
            deref_rval = struct.pack(">I", thread.xd) if instr.b_number == XD_REGISTER else \
                struct.pack(">I", thread.dx)
        else:
            deref_rval = struct.pack(">I", r_val)

        # Set A value based on mode
        if instr.a_mode == IMMEDIATE:
            self.core[l_val] = deref_rval
        elif instr.a_mode == RELATIVE:
            self.core[instr.a_number + thread.pc] = deref_rval
        elif instr.a_mode == REGISTER_DIRECT:
            if instr.a_number == XD_REGISTER:
                thread.xd = struct.unpack(">I", deref_rval)[0]
            else:
                thread.dx = struct.unpack(">I", deref_rval)[0]
        else:
            loc = thread.xd if instr.a_number == XD_REGISTER else thread.dx
            self.core[loc] = deref_rval

        # Set B value based on mode
        if instr.b_mode == IMMEDIATE:
            self.core[r_val] = deref_lval
        elif instr.b_mode == RELATIVE:
            self.core[instr.b_number + thread.pc] = deref_lval
        elif instr.b_mode == REGISTER_DIRECT:
            if instr.b_number == XD_REGISTER:
                thread.xd = struct.unpack(">I", deref_lval)[0]
            else:
                thread.dx = struct.unpack(">I", deref_lval)[0]
        else:
            loc = thread.xd if instr.b_number == XD_REGISTER else thread.dx
            self.core[loc] = deref_lval
        

    def syscall_handler(self, thread):
        """Parse and simulate a syscall.
        Syscalls are given arguments by the contents of XD and DX.
        XD contains the syscall number, while DX contains any optional arguments.
        If a syscall errors out, it will return the string "teey" in DX.
        Current syscalls:
        01: TRANSFER_OWNERSHIP - transfer ownership of the current thread to the player ID specified by DX
        02: LOCATE_NEAREST_THREAD - return the location of the nearest thread of a different owner in DX up to 50 bytes away
        """
        ERROR_CODE = "teey"
        num = thread.xd
        if num == TRANSFER_OWNERSHIP:
            if thread.dx in self.players.keys() and len(self.players[thread.xd].threads) < int(self.max_processes*1.5):
                self.players[thread.owner].threads.remove(thread.id)
                thread.owner = thread.dx
                self.players[thread.owner].threads.append(thread.id)
                sorted(self.players[thread.owner].threads)
            else:
                thread.dx = ERROR_CODE
            
        elif num == LOCATE_NEAREST_THREAD:
            all_threads = self.thread_pool + self.next_tick_pool
            closest_distance = self.core.size
            max_distance = 256
            closest_pc = None
            for t in all_threads:
                curr_distance = max(t.pc, thread.pc) - min(t.pc, thread.pc)
                if curr_distance < closest_distance and curr_distance <= max_distance and t.owner != thread.owner:
                    closest_distance = curr_distance
                    closest_pc = t.pc
            if closest_pc:
                thread.dx = closest_pc
            else:
                thread.dx = ERROR_CODE
            
        elif num == LOCATE_RANDOM_THREAD:
            all_threads = self.thread_pool + self.next_tick_pool
            all_threads.append(thread)
            max_distance = 1024
            in_range = [t for t in all_threads if max(t.pc, thread.pc) - min(t.pc, thread.pc) <= max_distance]
            thread.dx = choice(in_range).pc
            
        elif num == RANDOM_INT:
            thread.dx = randint(0, WORD_MAX)
                
        else:
            thread.dx = ERROR_CODE

    def spawn_thread_from_parent(self, pc, parent):
        """Create a new thread given a parent thread and place it in the next tick's thread pool.
        The child thread inherits everything from the parent except for its PC register and thread ID"""
        thread = deepcopy(parent)
        thread.pc = pc
        thread.id = self.thread_counter
        self.thread_counter += 1
        self.players[parent.owner].threads.append(thread.id)
        self.next_tick_pool.append(thread)
        self.update_thread_event_handler(thread.id, thread.pc, self.players[thread.owner].color)
    
    def spawn_new_thread(self, thread):
        """Create a new thread given a thread object and place it in the current thread pool."""
        thread = deepcopy(thread)
        if thread.id == -1:
            thread.id = self.thread_counter
            self.thread_counter += 1
        self.players[thread.owner].threads.append(thread.id)
        self.thread_pool.append(thread)
        self.update_thread_event_handler(thread.id, thread.pc, self.players[thread.owner].color)
        
    def tick(self):
        "Simulate one step for each thread in the thread pool"
        self.tick_event_handler()
        pool_size = len(self.thread_pool)
        if not pool_size:
            sleep(self.seconds_per_tick)
            
        while self.thread_pool:
            self.step(float(self.seconds_per_tick)/pool_size)
        self.thread_pool = self.next_tick_pool
        self.next_tick_pool = []
        self.tick_count += 1
        
    def step(self, sleep_length=None):
        """Simulate one step.
        """
        if len(self.thread_pool) == 0:
            if len(self.next_tick_pool) == 0:
                return
            self.thread_pool = self.next_tick_pool
            self.next_tick_pool = []
            self.tick_count += 1
        
        thread = self.thread_pool.pop(0)
        instr = Instruction()
        instr.mcode = [byte for byte in self.core[thread.pc : thread.pc + 4]]
        
        opc = instr.opcode
        
        self.players[thread.owner].score += 1
        if sleep_length:
            sleep(sleep_length)
            
        # copy the current instruction to the instruction register
        try:
            if (instr.a_mode == REGISTER_DIRECT or instr.a_mode == REGISTER_INDIRECT) and instr.a_number not in [0, 1]:
                raise yeetTimeException("a_number is not within the range of valid registers", thread, instr)
            if (instr.b_mode == REGISTER_DIRECT or instr.b_mode == REGISTER_INDIRECT) and instr.b_number not in [0, 1]:
                raise yeetTimeException("b_number is not within the range of valid registers", thread, instr)
            
            if opc == NOPE:
                # Not technically necessary, but might as well be explicit
                pass
            
            elif opc == YEET:
                self.mov_template(instr, thread, lambda x, y : x)
                
            elif opc == YOINK:
                self.mov_template(instr, thread, lambda x, y : y + x)
                
            elif opc == KNIOY:
                self.mov_template(instr, thread, lambda x, y : y - x)
                
            elif opc == MUL:
                self.mov_template(instr, thread, lambda x, y : y * x)
                
            elif opc == DIV:
                if self.get_a_int(instr, thread) == 0:
                    raise yeetTimeException("Divided by 0", thread, instr)
                self.mov_template(instr, thread, lambda x, y : y // x)
                    
            elif opc == FITS:
                if self.get_a_int(instr, thread) == 0:
                    raise yeetTimeException("Modulo by 0", thread, instr)
                self.mov_template(instr, thread, lambda x, y : y % x)
                
            elif opc == BOUNCE:
                self.jmp_template(thread, instr)
                return
                
            elif opc == BOUNCEZ:
                if self.get_a_int(instr, thread) == 0:
                    self.jmp_template(thread, instr)
                    return
                
            elif opc == BOUNCEN:
                if self.get_a_int(instr, thread) != 0:
                    self.jmp_template(thread, instr)
                    return
                
            elif opc == BOUNCED:
                if instr.a_mode != IMMEDIATE:
                    a = self.get_a_int(instr, thread) - 1
                else: 
                    # Immediates are treated as absolute addresses
                    a = struct.unpack(">I", self.core[instr.a_number : instr.a_number + INSTRUCTION_WIDTH])[0] - 1
                    
                if a < 0:
                    a = WORD_MAX - 1
                    
                if instr.a_mode == IMMEDIATE:
                    self.core[instr.a_number] = struct.pack(">I", a)
                elif instr.a_mode == RELATIVE:
                    self.core[instr.a_number + thread.pc] = struct.pack(">I", a)
                elif instr.a_mode == REGISTER_DIRECT:
                    if instr.a_number == 0:
                        thread.xd = a
                    else:
                        thread.dx = a
                elif instr.a_mode == REGISTER_INDIRECT:
                    if instr.a_number == 0:
                        self.core[thread.xd] = struct.pack(">I", a)
                    else:
                        self.core[thread.dx] = struct.pack(">I", a)
                if a != 0:
                    self.jmp_template(thread, instr)
                    return
                
            elif opc == ZOOP:
                # add one more to length of thread_pool to account for the current thread thats been popped
                if len(self.players[thread.owner].threads) < self.max_processes:
                    self.spawn_thread_from_parent(self.resolve_address(thread, instr), thread)
            
            elif opc == YEB:
                self.yeb_template(thread, instr)
                    
            elif opc == YEETCALL:
                self.syscall_handler(thread)
            
            else:
                raise yeetTimeException("Invalid instruction", thread, instr)
        except yeetTimeException as e:
            self.crash_thread(thread, e)
            return
                
        # Any instructions that altered control flow should have prematurely returned
        thread.pc = (thread.pc + INSTRUCTION_WIDTH) % self.core.size
        self.next_tick_pool.append(thread)
        self.update_thread_event_handler(thread.id, thread.pc, self.players[thread.owner].color)
