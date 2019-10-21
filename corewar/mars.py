#! /usr/bin/env python
# coding: utf-8

from copy import copy
from random import randint
import operator, struct

from core import Core
from yeetcode import *

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

    def __init__(self, core=None, minimum_separation=100,
                 randomize=True, max_processes=None):
        self.core = core if core else Core()
        self.minimum_separation = minimum_separation
        self.max_processes = max_processes if max_processes else len(self.core)
        self.thread_pool = []

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
            l_val = thread.xd_bytes if instr.a_number == 0 else thread.dx_bytes
        elif instr.a_mode == REGISTER_INDIRECT:
            loc = struct.unpack('>I', thread.xd_bytes)[0] if instr.a_number == 0 else struct.unpack('>I', thread.dx_bytes)[0]
            l_val = self.core[loc : loc + WORD_SIZE]
        else:
            print "shits fucked yo"
            # TODO: figure out how we want to handle errors
            return None
        return l_val
                        
    def get_a_int(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            l_val = instr.a_number
        elif instr.a_mode == RELATIVE:
            l_val = struct.unpack('>I', self.core[instr.a_number + thread.pc : instr.a_number + thread.pc + WORD_SIZE])[0]
        elif instr.a_mode == REGISTER_DIRECT:
            l_val = thread.xd if instr.a_number == 0 else thread.dx
        elif instr.a_mode == REGISTER_INDIRECT:
            loc = thread.xd if instr.a_number == 0 else thread.dx
            l_val = struct.unpack('>I', self.core[loc : loc + WORD_SIZE])[0]
        else:
            print "shits fucked yo"
            # TODO: figure out how we want to handle errors
            return None
        return l_val
                        
    def get_b_value(self, instr, thread):
        if instr.a_mode == IMMEDIATE:
            r_val = struct.pack('>H', instr.b_number)
        elif instr.a_mode == RELATIVE:
            r_val = self.core[instr.b_number + thread.pc : instr.b_number + thread.pc + WORD_SIZE]
        elif instr.a_mode == REGISTER_DIRECT:
            r_val = thread.xd_bytes if instr.b_number == 0 else thread.dx_bytes
        elif instr.a_mode == REGISTER_INDIRECT:
            loc = struct.unpack('>I', thread.xd_bytes)[0] if instr.b_number == 0 else struct.unpack('>I', thread.dx_bytes)[0]
            r_val = self.core[loc : loc + WORD_SIZE]
        else:
            print "shits fucked yo"
            # TODO: figure out how we want to handle errors
            return None
        return r_val
                        
    def get_b_int(self, instr, thread):
        if instr.b_mode == IMMEDIATE:
            r_val = instr.b_number
        elif instr.b_mode == RELATIVE:
            r_val = struct.unpack('>I', self.core[instr.b_number + thread.pc : instr.b_number + thread.pc + WORD_SIZE])[0]
        elif instr.b_mode == REGISTER_DIRECT:
            r_val = thread.xd if instr.b_number == 0 else thread.dx
        elif instr.b_mode == REGISTER_INDIRECT:
            loc = thread.xd if instr.b_number == 0 else thread.dx
            r_val = struct.unpack('>I', self.core[loc : loc + WORD_SIZE])[0]
        else:
            print "shits fucked yo"
            # TODO: figure out how we want to handle errors
            return None
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
            
        print "\n", l_int, r_int, instr.a_number, instr.b_number, thread.xd, thread.dx
        if instr.b_mode == IMMEDIATE:
            # Move into absolute address
            derefed_immediate = struct.unpack(struct_type, self.core[instr.b_number : instr.b_number + width])[0]
            self.core[instr.b_number] = struct.pack(struct_type, op(l_int, derefed_immediate) % max_size)
            self.core.owner[instr.b_number] = thread.owner
        elif instr.b_mode == RELATIVE:
            # Move into a relative offset
            self.core[instr.b_number + thread.pc] = struct.pack(struct_type, op(l_int, r_int) % max_size)
            self.core.owner[instr.b_number + thread.pc] = thread.owner
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
            self.core.owner[loc] = thread.owner
            
    def jmp_template(self, thread, loc):
        """Simulate a generic jump instruction
        """
        thread.pc = loc % core.size
        self.thread_pool.append(thread)
        
    def syscall_handler(self, thread):
        """Parse and simulate a syscall
        """
        # TODO: write code
        pass
        
    def step(self):
        """Simulate one step.
        """
        thread = self.thread_pool.pop(0)
        # copy the current instruction to the instruction register
        instr = Instruction()
        instr.mcode = [byte for byte in self.core[thread.pc : thread.pc + 4]]
        
        opc = instr.opcode
        print "start of step: ", thread.pc, instr.a_number, instr.b_number

        if opc == NOPE:
            # Not technically necessary, but might as well be explicit
            pass
        
        elif opc == YEET:
            self.mov_template(instr, thread, lambda x, y : x)
            
        elif opc == YOINK:
            print "yoinking"
            self.mov_template(instr, thread, lambda x, y : y + x)
            
        elif opc == SUB:
            self.mov_template(instr, thread, lambda x, y : y - x)
            
        elif opc == MUL:
            self.mov_template(instr, thread, lambda x, y : y * x)
            
        elif opc == DIV:
            if self.get_a_int(instr, thread) == 0:
                self.crash_thread()
                return
            self.mov_template(instr, thread, lambda x, y : y / x)
                
        elif opc == MOD:
            if self.get_a_value(instr, thread) == 0:
                self.crash_thread()
                return
            self.mov_template(instr, thread, lambda x, y : y % x)
            
        elif opc == BOUNCE:
            self.jmp_template(thread, self.get_b_value(instr, thread))
            
        elif opc == BOUNCEZ:
            if self.get_a_value(instr, thread) == 0:
                self.jmp_template(thread, self.get_b_value(instr, thread))
                return
            
        elif opc == BOUNCEN:
            if self.get_a_value(instr, thread) != 0:
                self.jmp_template(thread, self.get_b_value(instr, thread))
                return
            
        elif opc == BOUNCED:
            a = self.get_a_value(instr, thread) - 1
            if instr.b_mode == IMMEDIATE:
                self.jmp_template(thread, self.get_b_value(instr, thread))
                return
            elif instr.b_mode == RELATIVE:
                self.core[instr.a_number + thread.pc] = a
            elif instr.a_mode == REGISTER_DIRECT:
                if instr.a_number == 0:
                    thread.xd = a
                else:
                    thread.dx = a
            elif instr.a_mode == REGISTER_INDIRECT:
                if instr.a_number == 0:
                    self.core[thread.xd + thread.pc] = a
                else:
                    self.core[thread.dx + thread.pc] = a
            if a != 0:
                self.jmp_template(thread, self.get_b_value(instr, thread))
                return
            
        elif opc == ZOOP:
            # add one more to length of thread_pool to account for the current thread thats been popped
            if len(thread_pool) + 1 < self.max_processes:
                child = Thread(self.get_b_value(instr, thread) % self.core.size, thread.xd, thread.dx, thread.owner)
                self.thread_pool.append(child)
                
        elif opc == SLT:
            if self.get_a_value(instr, thread) < self.get_b_value(instr, thread):
                thread.pc += INSTRUCTION_WIDTH
                
        elif opc == SAMEZIES:
            if self.get_a_value(instr, thread) == self.get_b_value(instr, thread):
                thread.pc += INSTRUCTION_WIDTH
                
        elif opc == NSAMEZIES:
            if self.get_a_value(instr, thread) != self.get_b_value(instr, thread):
                thread.pc += INSTRUCTION_WIDTH
                
        elif opc == YEETCALL:
            syscall_handler(thread)
                
        # Any instructions that altered control flow should have prematurely returned
        thread.pc = (thread.pc + INSTRUCTION_WIDTH) % self.core.size
        self.thread_pool.append(thread)