# coding: utf-8

from copy import copy
import re

__all__ = ['parse', 'NOPE', 'YEET', 'YOINK', 'SUB', 'MUL', 'DIV', 'MOD', 'BOUNCE',
           'BOUNCEZ', 'BOUNCEN', 'BOUNCED', 'ZOOP', 'SLT', 'SAMEZIES', 'NSAMEZIES', 'YEETCALL',
           'IMMEDIATE', 'RELATIVE', 'REGISTER_DIRECT', 'REGISTER_INDIRECT', 'Instruction']

NOPE      = 0     # No operation
YEET      = 1     # move from A to B
YOINK     = 2     # add A to B, store result in B
SUB       = 3     # subtract A from B, store result in B
MUL       = 4     # multiply A by B, store result in B
DIV       = 5     # divide B by A, store result in B if A <> 0, else terminate
MOD       = 6     # divide B by A, store remainder in B if A <> 0, else terminate
BOUNCE    = 7     # transfer execution to A
BOUNCEZ   = 8     # transfer execution to A if B is zero
BOUNCEN   = 9     # transfer execution to A if B is non-zero
BOUNCED   = 10    # decrement B, if B is non-zero, transfer execution to A
ZOOP      = 11    # split off process to A
SLT       = 12    # skip next instruction if A is less than B
SAMEZIES  = 13    # Skip next instruction if A is equal to B
NSAMEZIES = 14    # Skip next instruction if A is not equal to B
YEETCALL  = 15    # System call

XD_REGISTER = 0
DX_REGISTER = 1

IMMEDIATE         = 0   # immediate
RELATIVE          = 1   # direct
REGISTER_DIRECT   = 2   # Register direct
REGISTER_INDIRECT = 3   # Register indirect

OPCODES = {'NOPE': NOPE, 'YEET': YEET, 'YOINK': YOINK, 'SUB': SUB, 'MUL': MUL,
           'DIV': DIV, 'MOD': MOD, 'BOUNCE': BOUNCE, 'BOUNCEZ': BOUNCEZ,
           'BOUNCEN': BOUNCEN, 'BOUNCED': BOUNCED, 'ZOOP': ZOOP, 'SLT': SLT,
           'SAMEZIES': SAMEZIES, 'NSAMEZIES': NSAMEZIES, 'YEETCALL': YEETCALL}

MODES = {'$': IMMEDIATE, '#': RELATIVE,
         '%': REGISTER_DIRECT, '[': REGISTER_INDIRECT}

REGISTERS = {'XD': XD_REGISTER, 'DX': DX_REGISTER}

NARGS = {'NOPE': 0, 'BOUNCE': 1, 'ZOOP': 1, 'YEETCALL': 1}

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
        opcode   = next(key for key,value in OPCODES.items() if value==self.opcode)
        a_mode   = next(key for key,value in MODES.items() if value==self.a_mode)
        b_mode   = next(key for key,value in MODES.items() if value==self.b_mode)

        return "%s %s %s, %s %s" % (opcode,
                                       a_mode,
                                       str(self.a_number).rjust(5),
                                       b_mode,
                                       str(self.b_number).rjust(5))

    def __repr__(self):
        return "<%s>" % self

def validate_arg(arg, mode):
    if arg[0] in MODES:
        arg = arg[1:]
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
    print(args)
    print(modes)
    try:
        args = [validate_arg(arg, mode) for (arg, mode) in zip(args, modes)]
    except Exception as e:
        raise e
    return [item for item in zip(args, modes)]

def parse_ysm(instr):
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
        raise Exception('%s: not enough args for instruction' % instr)
    a_arg = args[0][0] if args else None
    b_arg = args[1][0] if args and len(args) > 1 else None

    a_mode = args[0][1] if args else None
    b_mode = args[1][1] if args and len(args) > 1 else None
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
        # process labels
        if line.endswith(':'):
            labels[line.strip(':')] = len(instructions)
        
        instruction = parse_ysm(line)
        print(instruction)


    # # evaluate start expression
    # if isinstance(warrior.start, str):
    #     warrior.start = eval(warrior.start, environment, labels)

    # # second pass
    # for n, instruction in enumerate(warrior.instructions):

    #     # create a dictionary of relative labels addresses to be used as a local
    #     # eval environment
    #     relative_labels = dict((name, address-n) for name, address in labels.iteritems())

    #     # evaluate instruction fields using global environment and labels
    #     if isinstance(instruction.a_number, str):
    #         instruction.a_number = eval(instruction.a_number, environment, relative_labels)
    #     if isinstance(instruction.b_number, str):
    #         instruction.b_number = eval(instruction.b_number, environment, relative_labels)

    # return warrior

