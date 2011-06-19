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

class TestBytecode(object):
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