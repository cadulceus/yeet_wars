# coding: utf-8

from copy import copy
import re
from struct import pack

__all__ = ['parse', 'NOPE', 'YEET', 'YOINK', 'SUB', 'MUL', 'DIV', 'FITS', 'BOUNCE',
           'BOUNCEZ', 'BOUNCEN', 'BOUNCED', 'ZOOP', 'YEETCALL',
           'IMMEDIATE', 'RELATIVE', 'REGISTER_DIRECT', 'REGISTER_INDIRECT', 'Instruction',
           'TRANSFER_OWNERSHIP', 'LOCATE_NEAREST_THREAD', 'INSTRUCTION_WIDTH', 'WORD_SIZE',
           'WORD_MAX', 'BYTE_MAX']

# The instruction type is encoded in the first nibble of the first byte of the instruction
YEET      = 1     # move from A to B
YOINK     = 2     # add A to B, store result in B
SUB       = 3     # subtract A from B, store result in B
MUL       = 4     # multiply A by B, store result in B
DIV       = 5     # divide B by A, store result in B if A <> 0, else terminate
FITS       = 6     # divide B by A, store remainder in B if A <> 0, else terminate
BOUNCE    = 7     # transfer execution to B
BOUNCEZ   = 8     # transfer execution to B if A is zero
BOUNCEN   = 9     # transfer execution to B if A is non-zero
BOUNCED   = 10    # decrement A, if A is non-zero, transfer execution to B
ZOOP      = 11    # split off process to B
NOPE      = 14     # No operation
YEETCALL  = 15    # System call

# These values are encoded in the instruction as the a_number or b_number
XD_REGISTER = 0
DX_REGISTER = 1

# The mode being used for the a_number and b_number are encoded in the last nibble of the
# first byte of the instruction
IMMEDIATE         = 0   # immediate
RELATIVE          = 1   # direct
REGISTER_DIRECT   = 2   # Register direct
REGISTER_INDIRECT = 3   # Register indirect

# Syscall numbers
TRANSFER_OWNERSHIP      = 1 # transfer ownership of the current thread to the player ID specified by DX
LOCATE_NEAREST_THREAD   = 2 # return the location of the nearest thread of a different owner in DX

INSTRUCTION_WIDTH = 4
WORD_SIZE = 4
BYTE_MAX = 256
WORD_MAX = 4294967296

OPCODES = {'NOPE': NOPE, 'YEET': YEET, 'YOINK': YOINK, 'SUB': SUB, 'MUL': MUL,
           'DIV': DIV, 'FITS': FITS, 'BOUNCE': BOUNCE, 'BOUNCEZ': BOUNCEZ,
           'BOUNCEN': BOUNCEN, 'BOUNCED': BOUNCED, 'ZOOP': ZOOP, 'YEETCALL': YEETCALL}

MODES = {'$': IMMEDIATE, '#': RELATIVE,
         '%': REGISTER_DIRECT, '[': REGISTER_INDIRECT}

REGISTERS = {'XD': XD_REGISTER, 'DX': DX_REGISTER}

NARGS = {'YEETCALL': 0, 'NOPE': 0, 'BOUNCE': 1, 'ZOOP': 1}

class Instruction(object):
    "An encapsulation of a Redcode instruction."

    def __init__(self, opcode=None, a_mode=None, a_number=0,
                 b_mode=None, b_number=0):
        self.opcode = OPCODES[opcode.upper()] if isinstance(opcode, str) else opcode
        if a_mode is not None:
            self.a_mode = MODES[a_mode] if isinstance(a_mode, str) else a_mode
        else:
            self.a_mode = IMMEDIATE
        if b_mode is not None:
            self.b_mode = MODES[b_mode] if isinstance(b_mode, str) else b_mode
        else:
            self.b_mode = IMMEDIATE
        self._a_number = a_number if a_number else 0
        self._b_number = b_number if b_number else 0

        self.core = None
    
    @property
    def mcode(self):
        buf = []
        instruction_mcode = self.opcode << 4
        instruction_mcode |= self.a_mode << 2
        instruction_mcode |= self.b_mode
        buf.append(instruction_mcode)
        buf.append(self._a_number & 0xff)
        buf.append(self._b_number >> 8 & 0xff)
        buf.append(self._b_number & 0xff)
        return bytearray(buf)

    @mcode.setter
    def mcode(self, bytearray):
        if len(bytearray) != 4:
            raise Exception("%s: Byte array must have length of 4" % bytearray)
        for byte in bytearray:
            if not isinstance(byte, int) or byte < 0 or byte > 255:
                raise Exception("%s: Byte array must be ints" % bytearray)
        instruction = bytearray[0]
        self.opcode = instruction >> 4
        self.a_mode = (instruction >> 2) & 0x3
        self.b_mode = instruction & 0x3
        self._a_number = bytearray[1]
        self._b_number = bytearray[2] << 8 | bytearray[3]

    def core_binded(self, core):
        """Return a copy of this instruction binded to a Core.
        """
        instruction = copy(self)
        instruction.core = core
        return instruction

    @property
    def a_number(self):
        return self._a_number

    @property
    def b_number(self):
        return self._b_number

    @a_number.setter
    def a_number(self, number):
        self._a_number = self.core.trim_signed(number) if self.core else number

    @b_number.setter
    def b_number(self, number):
        self._b_number = self.core.trim_signed(number) if self.core else number

    def __eq__(self, other):
        return (self.opcode == other.opcode and self.a_mode == other.a_mode and
                self.a_number == other.a_number and self.b_mode == other.b_mode and 
                self.b_number == other.b_number)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        # inverse lookup the instruction values
        try:
            opcode   = next(key for key,value in OPCODES.items() if value==self.opcode)
            a_mode   = next(key for key,value in MODES.items() if value==self.a_mode)
            b_mode   = next(key for key,value in MODES.items() if value==self.b_mode)
        except Exception as e:
            return "UNPARSEABLE<%s>" % str(self.mcode).encode("hex")

        return "%s %s %s, %s %s" % (opcode,
                                       a_mode,
                                       str(self.a_number).rjust(5),
                                       b_mode,
                                       str(self.b_number).rjust(5))

    def __repr__(self):
        return "<%s>" % self

def validate_arg(arg, mode):
    """
    Validate an individual operand.
    Called by parse_operands.

    Example: parse_ysm('YEET %XD, 1337') would
    call parse_operands('%XD') which would then call
    validate_arg('XD', 2). validate_arg in this case
    would return 0 since that is the constant for the
    XD register.
    """
    if mode == REGISTER_INDIRECT and arg.endswith(']'):
        arg = arg[:-1]
    if mode == REGISTER_INDIRECT or mode == REGISTER_DIRECT:
        arg = arg.upper()
        if arg not in REGISTERS:
            raise Exception('%s: Invalid arg for register direct or indirect mode. Must be XD or DX.' % arg)
        return REGISTERS[arg]
    if arg.lower().startswith('0x'):
        arg = arg[2:]
        try:
            return int(arg, 16)
        except:
            pass
    try:
        return int(arg)
    except:
        pass
    try:
        return int(arg, 16)
    except:
        raise Exception('%s: Could not parse integer argument' % arg)

def parse_operands(operands):
    """
    Parse the operands of a yeetcode instruction.
    Everything after the opcode is the operands.
    Called by parse_ysm.
    Ex: parse_ysm('NOPE 1,2') would call
    parse_operands('1,2')
    """
    arg_a = None
    arg_b = None
    if not operands:
        return (arg_a, arg_b)
    args = [arg.strip() for arg in operands.split(',', 1)]
    if not args or not args[0]:
        raise Exception("%s: Failed parsing operands" % operands)
    modes = [MODES[arg[0]] if arg[0] in MODES else IMMEDIATE for arg in args]
    if len(args) != len(modes):
        raise Exception("%s: arg length and mode length mismatch" % operands)
    try:
        args = [validate_arg(arg[1:], mode) if arg[0] in MODES \
                else validate_arg(arg, mode) for (arg, mode) in zip(args, modes)]
    except Exception as e:
        raise e
    return [item for item in zip(args, modes)]

def parse_ysm(instr):
    """
    Parse a single yeetcode instruction and return 
    an instruction object. Ex: parse_ysm('NOPE 1,2')
    returns an instruction object: <NOPE $     1, $     2>
    """
    instr = instr.strip()
    parts = instr.split(None, 1)
    opcode = parts[0].upper()
    args = []
    if len(parts) > 1:
        try:
            args = parse_operands(parts[1])
        except Exception as e:
            raise e
    required_args = NARGS[opcode] if opcode in NARGS else 2
    if len(args) < required_args:
        raise Exception('%s: not enough args for instruction: expected args: %i, given: %i' % (instr, required_args, len(args)))
    if required_args == 2:
        a_arg = args[0][0]
        b_arg = args[1][0]

        a_mode = args[0][1]
        b_mode = args[1][1]
    elif required_args == 1:
        a_arg = a_mode = None
        b_arg = args[0][0]
        b_mode = args[0][1]
    elif required_args == 0:
        a_arg = b_arg = a_mode = b_mode = None
        
    return Instruction(
        opcode=opcode,
        a_mode=a_mode,
        a_number=a_arg,
        b_mode=b_mode,
        b_number=b_arg
    )

def parse(input, definitions={}):
    """ Parse a Redcode code from a line iterator (input) returning a Warrior
        object."""

    labels = {}
    instructions = []

    # use a version of environment because we're going to add names to it
    environment = copy(definitions)

    # first pass
    for n, line in enumerate(input):
        line = line.strip()
        if not line:
            continue
        # process info comments
        if line.startswith('#'):
            continue
        # allow for arbitrary 4 byte words
        if line.startswith('0x'):
            hex_str = line[2:]
            if len(hex_str) > 8:
                raise Exception('%s is too long to be contained in 4 bytes' % hex_str)
            instructions.append(pack(">I", int(hex_str, 16)))
            continue
        # process labels
        if line.endswith(':'):
            labels[line.strip(':')] = len(instructions)
        
        instruction = parse_ysm(line)
        instructions.append(instruction)
    return instructions
