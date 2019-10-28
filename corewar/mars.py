#! /usr/bin/env python
# coding: utf-8

from copy import copy
from random import randint
import operator, struct

from core import Core
from yeetcode import *
from players import *

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

class MARS(object):
    """The MARS. Encapsulates a simulation.
    """

    def __init__(self, core=None, minimum_separation=100, max_processes=20, players={}):
        self.core = core if core else Core()
        self.minimum_separation = minimum_separation
        self.max_processes = max_processes if max_processes else len(self.core)
        self.thread_pool = []
        self.next_tick_pool = []
        self.tick_count = 0
        self.players = players

    def __iter__(self):
        return iter(self.core)

    def __len__(self):
        return len(self.core)

    def __getitem__(self, address):
        return self.core[address]
    
    def crash_thread(self):
        # TODO: implement scoring for thread crashes
        pass
    
    def get_a_value(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            l_val = bytearray(instr.a_number)
        elif instr.a_mode == RELATIVE:
            l_val = self.core[instr.a_number + thread.pc : instr.a_number + thread.pc + WORD_SIZE]
        elif instr.a_mode == REGISTER_DIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                l_val = thread.xd_bytes if instr.a_number == 0 else thread.dx_bytes
            else:
                raise Exception("register a_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                loc = struct.unpack('>I', thread.xd_bytes)[0] if instr.a_number == 0 else struct.unpack('>I', thread.dx_bytes)[0]
                l_val = self.core[loc : loc + WORD_SIZE]
            else:
                raise Exception("register a_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
            
        else:
            raise Exception("a_mode is not within range: %s, instruction: %s" % (thread, instr))
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
                raise Exception("register a_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.a_number == 0 or instr.a_number == 1:
                loc = thread.xd if instr.a_number == 0 else thread.dx
                l_val = struct.unpack('>I', self.core[loc : loc + WORD_SIZE])[0]
            else:
                raise Exception("register a_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        else:
            raise Exception("a_mode is not within range: %s, instruction: %s" % (thread, instr))
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
                raise Exception("register b_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        elif instr.a_mode == REGISTER_INDIRECT:
            if instr.b_number == 0 or instr.b_number == 1:
                loc = struct.unpack('>I', thread.xd_bytes)[0] if instr.b_number == 0 else struct.unpack('>I', thread.dx_bytes)[0]
                r_val = self.core[loc : loc + WORD_SIZE]
            else:
                raise Exception("register b_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        else:
            raise Exception("b_mode is not within range: %s, instruction: %s" % (thread, instr))
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
                raise Exception("register b_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        elif instr.b_mode == REGISTER_INDIRECT:
            if instr.b_number == 0 or instr.b_number == 1:
                loc = thread.xd if instr.b_number == 0 else thread.dx
                r_val = struct.unpack('>I', self.core[loc : loc + WORD_SIZE])[0]
            else:
                raise Exception("register b_number is not 1 or 0 thread: %s, instruction: %s" % (thread, instr))
        else:
            raise Exception("b_mode is not within range: %s, instruction: %s" % (thread, instr))
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
            loc = thread.xd if instr.a_number == 0 else thread.dx
            self.core[loc] = struct.pack(struct_type, op(l_int, r_int) % max_size)
            self.core.owner[loc % self.core.size] = thread.owner
            
    def jmp_template(self, thread, instr):
        """Simulate a generic jump instruction
        """
        if instr.b_mode == IMMEDIATE:
            thread.pc = instr.b_number % self.core.size
        elif instr.b_mode == RELATIVE:
            thread.pc = thread.pc + instr.b_number % self.core.size
        elif instr.b_mode == REGISTER_DIRECT:
            loc = thread.xd if instr.b_number == 0 else thread.dx
            thread.pc = loc % self.core.size
        elif instr.b_mode == REGISTER_INDIRECT:
            loc = struct.unpack(">I", self.core[thread.xd : thread.xd + 4])[0] if \
                instr.b_number == 0 else \
                struct.unpack(">I", self.core[thread.dx : thread.dx + 4])[0]
            thread.pc = loc % self.core.size
        self.next_tick_pool.append(thread)
        
    def syscall_handler(self, thread):
        """Parse and simulate a syscall.
        Syscalls are given arguments by the contents of XD and DX.
        XD contains the syscall number, while DX contains any optional arguments.
        If a syscall errors out, it will return the string "teey" in DX.
        Current syscalls:
        01: TRANSFER_OWNERSHIP - transfer ownership of the current thread to the player ID specified by DX
        02: LOCATE_NEAREST_THREAD - return the location of the nearest thread of a different owner in DX
        """
        ERROR_CODE = "teey"
        num = thread.xd
        if num == TRANSFER_OWNERSHIP:
            if thread.dx in self.players.keys():
                thread.owner = thread.dx
            else:
                thread.dx = ERROR_CODE
            
        if num == LOCATE_NEAREST_THREAD:
            closest_distance = self.core.size
            closest_pc = None
            for t in self.thread_pool:
                curr_distance = max(t.pc, thread.pc) - min(t.pc, thread.pc)
                if curr_distance < closest_distance and t.owner != thread.owner:
                    closest_distance = curr_distance
                    closest_pc = t.pc
            if closest_pc:
                thread.dx = closest_pc
            else:
                thread.dx = ERROR_CODE
                    
            
        thread.pc = (thread.pc + 4) % self.core.size
        self.next_tick_pool.append(thread)

    def tick(self):
        "Simulate one step for each thread in the thread pool"
        while self.thread_pool:
            print self.thread_pool[0]
            self.step()
        self.thread_pool = self.next_tick_pool
        self.next_tick_pool = []
        self.tick_count += 1
        
    def step(self):
        """Simulate one step.
        """
        if len(self.thread_pool) == 0:
            if len(self.next_tick_pool) == 0:
                return
            self.thread_pool = self.next_tick_pool
            self.next_tick_pool = []
            self.tick_count += 1
        
        thread = self.thread_pool.pop(0)
        # copy the current instruction to the instruction register
        instr = Instruction()
        instr.mcode = [byte for byte in self.core[thread.pc : thread.pc + 4]]
        
        opc = instr.opcode
        try:
            if opc == NOPE:
                # Not technically necessary, but might as well be explicit
                pass
            
            elif opc == YEET:
                self.mov_template(instr, thread, lambda x, y : x)
                
            elif opc == YOINK:
                self.mov_template(instr, thread, lambda x, y : y + x)
                
            elif opc == SUB:
                self.mov_template(instr, thread, lambda x, y : y - x)
                
            elif opc == MUL:
                self.mov_template(instr, thread, lambda x, y : y * x)
                
            elif opc == DIV:
                if self.get_a_int(instr, thread) == 0:
                    raise Exception("Divided by 0 thread: %s, instr: %s" % (thread, instr))
                self.mov_template(instr, thread, lambda x, y : y / x)
                    
            elif opc == MOD:
                if self.get_a_value(instr, thread) == 0:
                    raise Exception("Modulo by 0 thread: %s, instr: %s" % (thread, instr))
                    return
                self.mov_template(instr, thread, lambda x, y : y % x)
                
            elif opc == BOUNCE:
                self.jmp_template(thread, instr)
                return
                
            elif opc == BOUNCEZ:
                if self.get_a_int(instr, thread) == 0:
                    self.jmp_template(thread, instr)
                    return
                
            elif opc == BOUNCEN:
                print thread, instr
                if self.get_a_int(instr, thread) != 0:
                    self.jmp_template(thread, instr)
                    return
                
            elif opc == BOUNCED:
                # TODO: HANDLE
                if instr.a_mode != IMMEDIATE:
                    a = self.get_a_int(instr, thread) - 1
                else: 
                    # Immediates are treated as absolute addresses
                    a = struct.unpack(">I", self.core[instr.a_number : instr.a_number + 4])[0] - 1
                    
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
                #TODO: make this check how many threads the PLAYER currently owns
                if len(self.thread_pool) < self.max_processes:
                    child = Thread(self.get_b_int(instr, thread) % self.core.size, thread.xd, thread.dx, thread.owner)
                    self.next_tick_pool.append(child)
                    
            elif opc == YEETCALL:
                self.syscall_handler(thread)
                return
            
            else:
                raise Exception("Invalid instruction: %s, instr: %s" % (thread, instr))
        except Exception as e:
            print "====THREAD CRASH====\n%s" % e
            self.crash_thread()
            return
                
        # Any instructions that altered control flow should have prematurely returned
        thread.pc = (thread.pc + INSTRUCTION_WIDTH) % self.core.size
        self.next_tick_pool.append(thread)