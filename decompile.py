import opcode


class Instruction(object):
    def __init__(self, opname, arg=None):
        self.opname = opname
        self.arg = arg

    def __eq__(self, other):
        if not isinstance(other, Instruction):
            return NotImplemented
        return self.opname == other.opname and self.arg == other.arg

def parse_bytecode(code):
    i = 0
    bytecodes = map(ord, code.co_code)
    instructions = []
    while i < len(bytecodes):
        op = bytecodes[i]
        i += 1
        arg = None
        if op >= opcode.HAVE_ARGUMENT:
            oparg = bytecodes[i] + (bytecodes[i + 1] << 8)
            i += 2
            if op in opcode.hasconst:
                arg = code.co_consts[oparg]
            else:
                raise NotImplementedError
        instructions.append(Instruction(
            opcode.opname[op],
            arg
        ))
    return instructions

class Literal(object):
    def __init__(self, obj):
        self.obj = obj

    def build(self):
        return str(self.obj)

class Interpreter(object):
    def __init__(self, instructions):
        self.instructions = instructions
        self.ops = []
        self.buf = []
        self.indent_level = 1

    def get_and_clear_buf(self, expected_len):
        assert len(self.buf) == expected_len
        buf = self.buf[:]
        del self.buf[:]
        return buf

    def emit(self, op):
        self.ops.append("    " * self.indent_level + op)

    def evaluate(self):
        for instr in self.instructions:
            handler = getattr(self, "handle_%s" % instr.opname)
            handler(instr)
        return "\n".join(self.ops)

    def handle_LOAD_CONST(self, instr):
        self.buf.append(Literal(instr.arg))

    def handle_RETURN_VALUE(self, instr):
        [obj] = self.get_and_clear_buf(1)
        self.emit("return %s" % obj.build())


def decompile(function):
    instructions = parse_bytecode(function.__code__)
    body = Interpreter(instructions).evaluate()
    header = "def %s():\n" % function.__name__
    return header + body