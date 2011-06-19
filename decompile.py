import contextlib
import opcode


NO_ARG = object()
class Instruction(object):
    def __init__(self, op, arg=NO_ARG, real_idx=None, new_idx=None):
        self.op = op
        self.opname = opcode.opname[op]
        self.arg = arg
        self.real_idx = real_idx
        self.new_idx = new_idx

    def __repr__(self):
        r = self.opname
        if self.arg is not NO_ARG:
            r += "(%s)" % self.arg
        return r

    def __eq__(self, other):
        if not isinstance(other, Instruction):
            return NotImplemented
        return self.opname == other.opname and self.arg == other.arg

    def finish(self, instructions):
        if self.op in opcode.hasjabs or self.op in opcode.hasjrel:
            for idx, instr in enumerate(instructions):
                if instr.real_idx == self.arg:
                    self.arg = idx
                    break
            else:
                assert False

def parse_bytecode(code):
    i = 0
    bytecodes = map(ord, code.co_code)
    instructions = []
    while i < len(bytecodes):
        op = bytecodes[i]
        opidx = i
        i += 1
        arg = NO_ARG
        if op >= opcode.HAVE_ARGUMENT:
            oparg = bytecodes[i] + (bytecodes[i + 1] << 8)
            i += 2
            if op in opcode.hasconst:
                arg = code.co_consts[oparg]
            elif op in opcode.hasname:
                arg = code.co_names[oparg]
            elif op in opcode.hasjabs:
                arg = oparg
            elif op in opcode.hasjrel:
                # Make it absolute
                arg = i + oparg
            else:
                raise NotImplementedError
        instructions.append(Instruction(
            op,
            arg,
            opidx,
            len(instructions),
        ))
    for instr in instructions:
        instr.finish(instructions)
    return instructions

class BasicBlock(object):
    def __init__(self):
        self.instructions = []

class BasicBlockFinder(object):
    def __init__(self, instructions):
        self.instructions = instructions
        self.pending_basic_blocks = {}
        self.starting_basic_block = self.pending_basic_blocks[0] = BasicBlock()

    def find_basic_blocks(self):
        current_basic_block = None
        for instr in self.instructions:
            if instr.new_idx in self.pending_basic_blocks:
                new_block = self.pending_basic_blocks.pop(instr.new_idx)
                current_basic_block = new_block
            handler = getattr(self, "handle_%s" % instr.opname)
            current_basic_block.instructions.append(instr)
            handler(instr)
        return self.starting_basic_block

    def get_basic_block(self, idx):
        # Could you try to get a block that was already completed?
        return self.pending_basic_blocks.setdefault(idx, BasicBlock())

    def handle_simple_op(self, instr):
        pass
    handle_LOAD_CONST = handle_LOAD_GLOBAL = handle_RETURN_VALUE = handle_POP_TOP = handle_simple_op

    def handle_POP_JUMP_IF_FALSE(self, instr):
        instr.true_block = self.get_basic_block(instr.new_idx + 1)
        instr.false_block = self.get_basic_block(instr.arg)

    def handle_JUMP_FORWARD(self, instr):
        instr.fallthrough = self.get_basic_block(instr.arg)


class Literal(object):
    def __init__(self, obj):
        self.obj = obj

    def build(self):
        return str(self.obj)

class AddBasicBlock(Exception):
    def __init__(self, block):
        self.block = block

class Interpreter(object):
    def __init__(self, basic_block, indent_level=1):
        self.basic_blocks = [basic_block]
        self.ops = []
        self.buf = []
        self.indent_level = indent_level

    def get_and_clear_buf(self, expected_len):
        assert len(self.buf) == expected_len
        buf = self.buf[:]
        del self.buf[:]
        return buf

    def emit(self, op):
        if isinstance(op, Interpreter):
            self.ops.append(op.evaluate())
        else:
            self.ops.append("    " * self.indent_level + op)

    @contextlib.contextmanager
    def indent(self):
        self.indent_level += 1
        try:
            yield
        finally:
            self.indent_level -= 1


    def evaluate(self):
        while self.basic_blocks:
            basic_block = self.basic_blocks.pop()
            self.handle_basic_block(basic_block)
        return "\n".join(self.ops)

    def handle_basic_block(self, basic_block):
        for instr in basic_block.instructions:
            handler = getattr(self, "handle_%s" % instr.opname)
            handler(instr)

    def handle_LOAD_CONST(self, instr):
        self.buf.append(Literal(instr.arg))

    def handle_LOAD_GLOBAL(self, instr):
        self.buf.append(Literal(instr.arg))

    def handle_RETURN_VALUE(self, instr):
        [obj] = self.get_and_clear_buf(1)
        self.emit("return %s" % obj.build())

    def handle_POP_TOP(self, instr):
        [obj] = self.get_and_clear_buf(1)
        self.emit(obj.build())

    def handle_POP_JUMP_IF_FALSE(self, instr):
        [obj] = self.get_and_clear_buf(1)
        self.emit("if %s:" % obj.build())
        with self.indent():
            self.handle_basic_block(instr.true_block)
        self.emit("else:")
        with self.indent():
            self.handle_basic_block(instr.false_block)

    def handle_JUMP_FORWARD(self, instr):
        self.basic_blocks.append(instr.fallthrough)


def decompile(function):
    instructions = parse_bytecode(function.__code__)
    start_bblock = BasicBlockFinder(instructions).find_basic_blocks()
    body = Interpreter(start_bblock).evaluate()
    header = "def %s():\n" % function.__name__
    return header + body