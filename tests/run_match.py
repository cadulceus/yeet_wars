from corewar.mars import *
from corewar.core import *
from corewar.players import *
from corewar.yeetcode import *
from struct import pack, unpack
from random import randint
import unittest

class InstructionTests(unittest.TestCase):
    def test_modifiers(self):
        mem = Core()
        runtime = MARS(mem, players={0: Player("Test", 0, "Token")})
        runtime.core[0] = parse(['YEET #0, #4'])[0].mcode
        runtime.spawn_new_thread(Thread(0, 0, 0, 0))
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x15\x00\x00\x04\x15\x00\x00\x04\x00\x00\x00\x00')
        
        runtime.core[4] = parse(['YEET $8, $81'])[0].mcode
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x15\x00\x00\x04\x10\x08\x00\x51\x00\x00\x00\x00')
        self.assertEqual(runtime.core[81], 8)
        
        runtime.thread_pool = [Thread(0, parse(['YEET %XD, %DX'])[0].mcode, 0, 0)]
        runtime.core[0] = parse(['YEET %XD, $4'])[0].mcode
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x18\x00\x00\x04\x1A\x00\x00\01\x00\x00\x00\x00')
        self.assertEqual(runtime.next_tick_pool[0].xd, runtime.next_tick_pool[0].dx)
        
        runtime.core[0] = parse(['YEET [DX, $80'])[0].mcode
        runtime.core[12] = 'YEET'
        runtime.next_tick_pool = [Thread(0, 0, '\x00\x00\x00\x0C', 0)]
        runtime.step()
        self.assertEqual(runtime.core[80:84], 'YEET')
        
    def test_yeet(self):
        mem = Core()
        runtime = MARS(mem, players={0: Player("Test", 0, "Token")})
        runtime.core[0] = parse(['YEET #0, #4'])[0].mcode
        runtime.spawn_new_thread(Thread(0, 0, 0, 0))
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x15\x00\x00\x04\x15\x00\x00\x04\x00\x00\x00\x00')
        self.assertEqual(runtime.next_tick_pool[0].pc, 4)
        self.assertEqual(runtime.next_tick_pool[0].xd, 0)
        self.assertEqual(runtime.next_tick_pool[0].dx, 0)
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x15\x00\x00\x04\x15\x00\x00\x04\x15\x00\x00\x04')
        self.assertEqual(runtime.next_tick_pool[0].pc, 8)
        self.assertEqual(runtime.next_tick_pool[0].xd, 0)
        self.assertEqual(runtime.next_tick_pool[0].dx, 0)
        self.assertEqual(len(runtime.next_tick_pool), 1)
        
    def test_math(self):
        mem = Core()
        runtime = MARS(mem, players={0: Player("Test", 0, "Token")})
        instrs = parse(['YOINK $3, #50', 'SUB $5, $100', 'MUL $7, %XD', 'DIV $11, [DX', 'FITS $13, $200', 'DIV $0, $250'])
        initial_core = ""
        for instr in instrs:
            initial_core += instr.mcode
            
        runtime.core[0] = initial_core
        runtime.core[50] = pack('>B', 17)
        runtime.core[100] = pack('>B', 21)
        runtime.core[150] = pack('>B', 23)
        runtime.core[200] = pack('>B', 29)
        runtime.core[250] = pack('>I', 37) #redundant, but explicit
        
        runtime.spawn_new_thread(Thread(0, 31, 150, 0))
        runtime.step()
        self.assertEqual(runtime.core[50], 3 + 17)
        runtime.step()
        self.assertEqual(runtime.core[100], 21 - 5)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].xd, 31 * 7)
        runtime.step()
        self.assertEqual(runtime.core[150], 23 / 11)
        runtime.step()
        self.assertEqual(runtime.core[200], 29 % 13)
        runtime.step()
        self.assertEqual(len(runtime.next_tick_pool), 0) # thread should have crashed  
        
    def test_jmp(self):
        mem = Core()
        runtime = MARS(mem, players={0: Player("Test", 0, "Token")})
        instrs = parse(['BOUNCE $8',
                        'NOPE',
                        'BOUNCEZ %XD, [DX',
                        'BOUNCEN %DX, #8',
                        'NOPE',
                        'BOUNCED [DX, #0',
                        'BOUNCED $60, $0'])
        initial_core = ""
        for instr in instrs:
            initial_core += instr.mcode
            
        runtime.core[0] = initial_core
        runtime.core[50] = pack('>I', 5)
        runtime.core[60] = pack('>I', 0) # unnecessary but explicit
        
        runtime.spawn_new_thread(Thread(0, 1, 50, 0))
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 8)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 12)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 20)
        for i in range(1, 5):
            runtime.step()
            self.assertEqual(unpack(">I", runtime.core[50:54])[0], 5 - i)
            self.assertEqual(runtime.next_tick_pool[0].pc, 20)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 24)
        self.assertEqual(unpack(">I", runtime.core[50:54])[0], 0)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 0)
        self.assertEqual(unpack(">I", runtime.core[60:64])[0], WORD_MAX - 1)
        
    def test_split(self):
        mem = Core()
        runtime = MARS(mem, players={0: Player("Test", 0, "Token")})
        instrs = parse(['ZOOP $8',
                        'NOPE',
                        'ZOOP %DX',
                        'ZOOP [XD',
                        'ZOOP #0',
                        'NOPE',
                        'NOPE'])
        initial_core = ""
        for instr in instrs:
            initial_core += instr.mcode
            
        runtime.core[0] = initial_core
        runtime.core[50] = pack('>I', 20)
        
        runtime.spawn_new_thread(Thread(0, 50, 12, 0))
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 8)
        self.assertEqual(runtime.next_tick_pool[1].pc, 4)
        self.assertEqual(len(runtime.next_tick_pool), 2)
        self.assertEqual(len(runtime.thread_pool), 0)
        runtime.step()
        self.assertEqual(runtime.thread_pool[0].pc, 4)
        self.assertEqual(runtime.next_tick_pool[0].pc, 12)
        self.assertEqual(runtime.next_tick_pool[1].pc, 12)
        self.assertEqual(len(runtime.thread_pool), 1)
        self.assertEqual(len(runtime.next_tick_pool), 2)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[0].pc, 12)
        self.assertEqual(runtime.next_tick_pool[1].pc, 12)
        self.assertEqual(runtime.next_tick_pool[2].pc, 8)
        self.assertEqual(len(runtime.thread_pool), 0)
        self.assertEqual(len(runtime.next_tick_pool), 3)
        runtime.step()
        self.assertEqual(runtime.thread_pool[0].pc, 12)
        self.assertEqual(runtime.thread_pool[1].pc, 8)
        self.assertEqual(runtime.next_tick_pool[0].pc, 20)
        self.assertEqual(runtime.next_tick_pool[1].pc, 16)
        self.assertEqual(len(runtime.thread_pool), 2)
        self.assertEqual(len(runtime.next_tick_pool), 2)
        runtime.step()
        self.assertEqual(runtime.thread_pool[0].pc, 8)
        self.assertEqual(runtime.next_tick_pool[0].pc, 20)
        self.assertEqual(runtime.next_tick_pool[1].pc, 16)
        self.assertEqual(runtime.next_tick_pool[2].pc, 20)
        self.assertEqual(runtime.next_tick_pool[3].pc, 16)
        self.assertEqual(len(runtime.thread_pool), 1)
        self.assertEqual(len(runtime.next_tick_pool), 4)
 
    def test_syscall(self):
        runtime = MARS(players={0 : Player("yeet", 0, "Token1"), 1 : Player("rando", 1, "Token2"), 69 : Player("teey", 69, "Token3")})
        instrs = parse(['YEETCALL'])
        initial_core = ""
        for instr in instrs:
            initial_core += instr.mcode
            
        runtime.core[0] = initial_core
        
        runtime.spawn_new_thread(Thread(0, LOCATE_NEAREST_THREAD, 0, 0))
        runtime.spawn_new_thread(Thread(0, TRANSFER_OWNERSHIP, 42, 0)) # attempt to transfer to non existent player
        runtime.spawn_new_thread(Thread(0, TRANSFER_OWNERSHIP, 69, 0)) # transfer ownership from yeet to teey
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[-1].pc, 4)
        self.assertEqual(runtime.next_tick_pool[-1].owner, 69)
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[-1].pc, 4)
        self.assertEqual(runtime.next_tick_pool[-1].owner, 0)
        self.assertEqual(runtime.next_tick_pool[-1].dx_bytes, "teey")
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[-1].pc, 4)
        self.assertEqual(runtime.next_tick_pool[-1].dx_bytes, "teey")
        runtime.thread_pool = []
        runtime.spawn_new_thread(Thread(50, LOCATE_NEAREST_THREAD, 0, 1))
        runtime.spawn_new_thread(Thread(20, LOCATE_NEAREST_THREAD, 0, 1))
        runtime.spawn_new_thread(Thread(10, LOCATE_NEAREST_THREAD, 0, 0))
        runtime.spawn_new_thread(Thread(0, LOCATE_NEAREST_THREAD, 0, 0))
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[-1].pc, 4)
        self.assertEqual(runtime.next_tick_pool[-1].dx, 20)
        runtime.thread_pool = []
        runtime.spawn_new_thread(Thread(10, LOCATE_NEAREST_THREAD, 0, 0))
        runtime.spawn_new_thread(Thread(0, LOCATE_NEAREST_THREAD, 0, 0))
        runtime.step()
        self.assertEqual(runtime.next_tick_pool[-1].pc, 4)
        self.assertEqual(runtime.next_tick_pool[-1].dx_bytes, "teey")
        
    def test_fuzz(self):
        runtime = MARS(players={0 : Player("rando1", 0, "Token1"), 1 : Player("rando2", 1, "Token2"), 2 : Player("rando3", 2, "Token3")})
        initial_core = ""
        for i in range(runtime.core.size):
            initial_core += chr(randint(0, 255))
            if i % 7 == 0:
                xd = randint(0, WORD_MAX - 1) if randint(0, 1) else randint(0, BYTE_MAX - 1)
                dx = randint(0, WORD_MAX - 1) if randint(0, 1) else randint(0, BYTE_MAX - 1)
                runtime.spawn_new_thread(Thread(i, xd, dx, randint(0, 2)))
            
        runtime.core[0] = initial_core
        for i in range(200000):
            cycle_count = i
            live_threads = len(runtime.thread_pool) + len(runtime.next_tick_pool)
            runtime.step()
            if len(runtime.thread_pool) + len(runtime.next_tick_pool) == 0:
                break
        print "Test completed in %s cycles, %s threads remained" % (cycle_count, live_threads)
        for thread in runtime.thread_pool: print thread, disassemble(runtime.core[thread.pc:thread.pc + 4])
        for thread in runtime.next_tick_pool: print thread, disassemble(runtime.core[thread.pc:thread.pc + 4])
 
def run_tests():
    unittest.main()
    
if __name__ == '__main__':
    unittest.main()