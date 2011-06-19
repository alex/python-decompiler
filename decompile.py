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
        if self.op in opcode.hasjabs:
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

class Literal(object):
    def __init__(self, obj):
        self.obj = obj

    def build(self):
        return str(self.obj)

class Interpreter(object):
    def __init__(self, instructions, start_instr, stop_instr, indent_level=1):
        self.instructions = instructions
        self.ops = []
        self.buf = []
        self.current_instr = start_instr
        self.stop_instr = stop_instr
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

    def evaluate(self):
        while self.current_instr < self.stop_instr:
            current_instr = self.current_instr
            instr = self.instructions[current_instr]
            handler = getattr(self, "handle_%s" % instr.opname)
            handler(instr)
            # The current instruction was unchanged by the handler, we need to
            # bump it.
            if self.current_instr == current_instr:
                self.current_instr += 1
        return "\n".join(self.ops)

    def handle_LOAD_CONST(self, instr):
        self.buf.append(Literal(instr.arg))

    def handle_LOAD_GLOBAL(self, instr):
        self.buf.append(Literal(instr.arg))

    def handle_RETURN_VALUE(self, instr):
        [obj] = self.get_and_clear_buf(1)
        self.emit("return %s" % obj.build())

    def handle_POP_JUMP_IF_FALSE(self, instr):
        [obj] = self.get_and_clear_buf(1)
        self.emit("if %s:" % obj.build())
        self.emit(Interpreter(
            self.instructions,
            instr.new_idx + 1,
            instr.arg,
            self.indent_level + 1
        ))
        self.emit("else:")
        self.emit(Interpreter(
            self.instructions,
            instr.arg,
            len(self.instructions),
            self.indent_level + 1,
        ))
        self.current_instr = len(self.instructions)

def decompile(function):
    instructions = parse_bytecode(function.__code__)
    body = Interpreter(instructions, 0, len(instructions)).evaluate()
    header = "def %s():\n" % function.__name__
    return header + body