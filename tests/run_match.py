from corewar.mars import *
from corewar.core import *
from corewar.players import *
from corewar.yeetcode import *
from struct import pack, unpack
import unittest

class InstructionTests(unittest.TestCase):
    def test_modifiers(self):
        mem = Core()
        runtime = MARS(mem)
        runtime.core[0] = parse(['YEET #0, #4'])[0].mcode
        runtime.thread_pool.append(Thread(0, 0, 0, 0))
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
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x18\x00\x00\x04\x1A\x00\x00\01\x00\x00\x00\x00')
        self.assertEqual(runtime.thread_pool[0].xd, runtime.thread_pool[0].dx)
        
        runtime.core[0] = parse(['YEET [DX, $80'])[0].mcode
        runtime.core[12] = 'YEET'
        runtime.thread_pool = [Thread(0, 0, '\x00\x00\x00\x0C', 0)]
        runtime.step()
        self.assertEqual(runtime.core[80:84], 'YEET')
        
    def test_yeet(self):
        mem = Core()
        runtime = MARS(mem)
        runtime.core[0] = parse(['YEET #0, #4'])[0].mcode
        runtime.thread_pool.append(Thread(0, 0, 0, 0))
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x15\x00\x00\x04\x15\x00\x00\x04\x00\x00\x00\x00')
        self.assertEqual(runtime.thread_pool[0].pc, 4)
        self.assertEqual(runtime.thread_pool[0].xd, 0)
        self.assertEqual(runtime.thread_pool[0].dx, 0)
        runtime.step()
        self.assertEqual(runtime.core[:12], '\x15\x00\x00\x04\x15\x00\x00\x04\x15\x00\x00\x04')
        self.assertEqual(runtime.thread_pool[0].pc, 8)
        self.assertEqual(runtime.thread_pool[0].xd, 0)
        self.assertEqual(runtime.thread_pool[0].dx, 0)
        self.assertEqual(len(runtime.thread_pool), 1)
        
    def test_math(self):
        mem = Core()
        runtime = MARS(mem)
        instrs = parse(['YOINK $3, #50', 'SUB $5, $100', 'MUL $7, %XD', 'DIV $11, [DX', 'MOD $13, $200', 'DIV $0, $250'])
        initial_core = ""
        for instr in instrs:
            initial_core += instr.mcode
            
        runtime.core[0] = initial_core
        runtime.core[50] = pack('>B', 17)
        runtime.core[100] = pack('>B', 21)
        runtime.core[150] = pack('>B', 23)
        runtime.core[200] = pack('>B', 29)
        runtime.core[250] = pack('>I', 37) #redundant, but explicit
        
        runtime.thread_pool.append(Thread(0, 31, 150, 0))
        runtime.step()
        self.assertEqual(runtime.core[50], 3 + 17)
        runtime.step()
        self.assertEqual(runtime.core[100], 21 - 5)
        runtime.step()
        self.assertEqual(runtime.thread_pool[0].xd, 31 * 7)
        runtime.step()
        self.assertEqual(runtime.core[150], 23 / 11)
        runtime.step()
        self.assertEqual(runtime.core[200], 29 % 13)
        runtime.step()
        self.assertEqual(len(runtime.thread_pool), 0) # thread should have crashed
        
def run_tests():
    unittest.main()
    
if __name__ == '__main__':
    unittest.main()