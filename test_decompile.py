import opcode
import textwrap

from decompile import decompile, parse_bytecode, Instruction


class TestDecompilation(object):
    def assert_decompiles(self, func, expected):
        result = decompile(func)
        expected = textwrap.dedent(expected).strip("\n")
        assert result == expected

    def test_simple(self):
        def f():
            return 1

        self.assert_decompiles(f, """
            def f():
                return 1
        """)

    def test_branch(self):
        def f():
            if z:
                return 1
            else:
                return 2

        # This needs some dead code eliminiation applied to it.
        self.assert_decompiles(f, """
            def f():
                if z:
                    return 1
                else:
                    return 2
                    return None
        """)

    def test_more_branchy_stuff(self):
        def f():
            if z:
                x
            else:
                y
            return 2

        self.assert_decompiles(f, """
            def f():
                if z:
                    x
                else:
                    y
                return 2
        """)

    def test_simple_parameters(self):
        def f(a):
            return a

        self.assert_decompiles(f, """
            def f(a):
                return a
        """)

    def test_list_ops(self):
        def f():
            x = []
            x.append(1)
            x[0] = 3

        self.assert_decompiles(f, """
            def f():
                x = []
                x.append(1)
                x[0] = 3
                return None
        """)

    def test_simple_for_loop(self):
        def f(x):
            for i in x:
                pass

        # TODO: continue should become pass where possible
        self.assert_decompiles(f, """
            def f(x):
                for i in x:
                    continue
                return None
        """)

class TestBytecodeParser(object):
    def assert_bytecode(self, func, expected):
        instructions = parse_bytecode(func.__code__)
        expected = [
            Instruction(opcode.opmap[args[0]], *args[1:])
            for args in expected
        ]
        assert instructions == expected

    def test_simple(self):
        def f():
            return 1

        self.assert_bytecode(f, [
            ("LOAD_CONST", 1),
            ("RETURN_VALUE",),
        ])

    def test_load_global(self):
        def f():
            return z

        self.assert_bytecode(f, [
            ("LOAD_GLOBAL", "z"),
            ("RETURN_VALUE",),
        ])

    def test_simple_branch(self):
        def f():
            if z:
                return 1
            else:
                return 2

        self.assert_bytecode(f, [
            ("LOAD_GLOBAL", "z"),
            ("POP_JUMP_IF_FALSE", 4),
            ("LOAD_CONST", 1),
            ("RETURN_VALUE",),
            ("LOAD_CONST", 2),
            ("RETURN_VALUE",),
            ("LOAD_CONST", None),
            ("RETURN_VALUE",)
        ])

    def test_jump_forward(self):
        def f():
            if z:
                x
            else:
                y
            return 1

        self.assert_bytecode(f, [
            ("LOAD_GLOBAL", "z"),
            ("POP_JUMP_IF_FALSE", 5),
            ("LOAD_GLOBAL", "x"),
            ("POP_TOP",),
            ("JUMP_FORWARD", 7),
            ("LOAD_GLOBAL", "y"),
            ("POP_TOP",),
            ("LOAD_CONST", 1),
            ("RETURN_VALUE",)
        ])

    def test_parameter_name(self):
        def f(a):
            return a

        self.assert_bytecode(f, [
            ("LOAD_FAST", "a"),
            ("RETURN_VALUE",)
        ])