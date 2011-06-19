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

class TestBytecode(object):
    def assert_bytecodes(self, func, expected):
        assert parse_bytecode(func.__code__) == expected

    def test_simple(self):
        def f():
            return 1

        self.assert_bytecodes(f, [
            Instruction("LOAD_CONST", 1),
            Instruction("RETURN_VALUE",)
        ])