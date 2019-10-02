#! /usr/bin/env python
# coding: utf-8

from copy import copy
import operator
from random import randint

from core import Core, DEFAULT_INITIAL_INSTRUCTION
from redcode import *

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

    def reset(self, clear_instruction=DEFAULT_INITIAL_INSTRUCTION):
        "Clears core and re-loads warriors."
        self.core.clear(clear_instruction)
        self.load_warriors()

    def load_warriors(self, randomize=True):
        "Loads its warriors to the memory with starting task queues"

        # the space between warriors - equally spaced in the core
        space = len(self.core) / len(self.warriors)

        for n, warrior in enumerate(self.warriors):
            # position is in the nth equally separated space plus a random
            # shift up to where the last instruction is minimum separated from
            # the first instruction of the next warrior
            warrior_position = (n * space)

            if randomize:
                warrior_position += randint(0, max(0, space -
                                                      len(warrior) -
                                                      self.minimum_separation))

            # add first and unique warrior task
            warrior.task_queue = [self.core.trim(warrior_position + warrior.start)]

            # copy warrior's instructions to the core
            for i, instruction in enumerate(warrior.instructions):
                self.core[warrior_position + i] = copy(instruction)
                self.core_event(warrior, warrior_position + i, EVENT_I_WRITE)

    def enqueue(self, warrior, address):
        """Enqueue another process into the warrior's task queue. Only if it's
           not already full.
        """
        if len(warrior.task_queue) < self.max_processes:
            warrior.task_queue.append(self.core.trim(address))

    def __iter__(self):
        return iter(self.core)

    def __len__(self):
        return len(self.core)

    def __getitem__(self, address):
        return self.core[address]
    
    def crash_thread():
        # TODO: implement scoring for thread crashes
        pass
    
    def get_a_value(instr):
        if instr.a_mode == IMMEDIATE
            l_val = instr.a_number
        elif instr.a_mode == RELATIVE
            l_val = self.core.trim(instr.a_number + thread.pc)
        elif instr.a_mode == REGISTER_DIRECT
            l_val = thread.xd if instr.a_number == 0 else thread.dx
        elif instr.a_mode == REGISTER_INDIRECT
            l_val = self.core[self.core.trim(thread.xd)] if instr.a_number == 0 \
                        else self.core[self.core.trim(thread.dx)]
        else
            # TODO: figure out how we want to handle errors
            return l_val
                        
    def get_b_value(instr):
        if instr.a_mode == IMMEDIATE
            r_val = instr.b_number
        elif instr.a_mode == RELATIVE
            r_val = self.core.trim(instr.b_number + thread.pc)
        elif instr.a_mode == REGISTER_DIRECT
            r_val = thread.xd if instr.b_number == 0 else thread.dx
        elif instr.a_mode == REGISTER_INDIRECT
            r_val = self.core[self.core.trim(thread.xd)] if instr.b_number == 0 \
                        else self.core[self.core.trim(thread.dx)]
        else
            # TODO: figure out how we want to handle errors
            return r_val
        
    def mov_template(instr, thread, val)
        """Simulate a move instruction
        """
        if instr.b_mode == IMMEDIATE
            # Move into absolute address
            self.core[self.core.trim(instr.b_number)] = val
        elif instr.b_mode == RELATIVE
            # Move into a relative offset
            self.core[self.core.trim(instr.b_number + thread.pc)] = val
        elif instr.a_mode == REGISTER_DIRECT
            # Move into a register
            if instr.b_number == 0:
                thread.xd = val
            else:
                thread.dx = val
        elif instr.a_mode == REGISTER_INDIRECT
            # Move into an absolute address held by a register
            if instr.b_number == 0:
                loc = thread.xd
            else:
                loc = thread.dx
            self.core[self.core.trim(loc)] = val
            
    
        
    def step(self):
        """Simulate one step.
        """
        thread = self.thread_pool.pop(0)
        # copy the current instruction to the instruction register
        instr = yeetcode.Instruction()
        instr.mcode = [self.core[(thread.pc + i) % len(self.core)] for i in range(4)]
        
        opc = instr.opcode

        if opc == NOPE:
            # Not technically necessary, but might as well be explicit
            pass
        elif opc == YEET:
            mov_template(instr, thread, get_a_value())
            
        elif opc == YOINK:
            mov_template(instr, thread, get_b_value() + get_a_value())
            
        elif opc == SUB:
            mov_template(instr, thread, get_b_value() - get_a_value())
            
        elif opc == MUL:
            mov_template(instr, thread, get_b_value() * get_a_value())
            
        elif opc == DIV:
            a = get_a_value()
            if a == 0:
                crash_thread()
                return
            mov_template(instr, thread, get_b_value() / a)
                
        elif opc == MOD:
            a = get_a_value()
            if a == 0:
                crash_thread()
                return
            mov_template(instr, thread, get_b_value() % a)
                
        # Any instructions that altered control flow should have prematurely returned
        thread.pc += INSTRUCTION_WIDTH
        thread.pc = self.core.trim(thread.pc)
        thread_pool.append(thread)

if __name__ == "__main__":
    import argparse
    import redcode

    parser = argparse.ArgumentParser(description='MARS (Memory Array Redcode Simulator)')
    parser.add_argument('--rounds', '-r', metavar='ROUNDS', type=int, nargs='?',
                        default=1, help='Rounds to play')
    parser.add_argument('--size', '-s', metavar='CORESIZE', type=int, nargs='?',
                        default=8000, help='The core size')
    parser.add_argument('--cycles', '-c', metavar='CYCLES', type=int, nargs='?',
                        default=80000, help='Cycles until tie')
    parser.add_argument('--processes', '-p', metavar='MAXPROCESSES', type=int, nargs='?',
                        default=8000, help='Max processes')
    parser.add_argument('--length', '-l', metavar='MAXLENGTH', type=int, nargs='?',
                        default=100, help='Max warrior length')
    parser.add_argument('--distance', '-d', metavar='MINDISTANCE', type=int, nargs='?',
                        default=100, help='Minimum warrior distance')
    parser.add_argument('warriors', metavar='WARRIOR', type=file, nargs='+',
                        help='Warrior redcode filename')

    args = parser.parse_args()

    # build environment
    environment = {'CORESIZE': args.size,
                   'CYCLES': args.cycles,
                   'ROUNDS': args.rounds,
                   'MAXPROCESSES': args.processes,
                   'MAXLENGTH': args.length,
                   'MINDISTANCE': args.distance}

    # assemble warriors
    warriors = [redcode.parse(file, environment) for file in args.warriors]

    # initialize wins, losses and ties for each warrior
    for warrior in warriors:
        warrior.wins = warrior.ties = warrior.losses = 0

    # for each round
    for i in xrange(args.rounds):

        # create new simulation
        simulation = MARS(warriors=warriors,
                          minimum_separation = args.distance,
                          max_processes = args.processes)

        active_warrior_to_stop = 1 if len(warriors) >= 2 else 0

        for c in xrange(args.cycles):
            simulation.step()

            # if there's only one left, or are all dead, then stop simulation
            if sum(1 if warrior.task_queue else 0 for warrior in warriors) <= active_warrior_to_stop:
                for warrior in warriors:
                    if warrior.task_queue:
                        warrior.wins += 1
                    else:
                        warrior.losses += 1
                break
        else:
            # running until max cycles: tie
            for warrior in warriors:
                if warrior.task_queue:
                    warrior.ties += 1
                else:
                    warrior.losses += 1

    # print results
    print "Results: (%d rounds)" % args.rounds
    print "%s %s %s %s" % ("Warrior (Author)".ljust(40), "wins".rjust(5),
                           "ties".rjust(5), "losses".rjust(5))
    for warrior in warriors:
        print "%s %s %s %s" % (("%s (%s)" % (warrior.name, warrior.author)).ljust(40),
                               str(warrior.wins).rjust(5),
                               str(warrior.ties).rjust(5),
                               str(warrior.losses).rjust(5))


