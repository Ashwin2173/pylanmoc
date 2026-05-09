from utils.enums import TokenType, StatementType

class Word:
    def __init__(self, w_raw: str, w_type: TokenType, w_line: int, w_span: tuple[int, int]):
        self.w_raw = w_raw
        self.w_type = w_type
        self.w_line = w_line
        self.w_span = w_span

    def get_raw(self) -> str:
        return self.w_raw

    def get_type(self) -> TokenType:
        return self.w_type

    def get_line(self) -> int:
        return self.w_line

    def get_span(self) -> tuple[int, int]:
        return self.w_span

    def __str__(self):
        return f"{self.w_type} '{self.w_raw}' at line: {self.w_line}"

class Statement:
    def __init__(self, s_type: StatementType, s_line: int) -> None:
        self.s_type = s_type
        self.s_line = s_line

    def get_type(self) -> StatementType:
        return self.s_type

    def get_line(self) -> int:
        return self.s_line

class ReturnStatement(Statement):
    def __init__(self, expression: Statement, line: int) -> None:
        super().__init__(StatementType.RETURN_STATEMENT, line)
        self.expression = expression

class BlockStatement(Statement):
    def __init__(self, body: list[Statement], line: int) -> None:
        super().__init__(StatementType.BLOCK_STATEMENT, line)
        self.body = body

class FunctionStatement(Statement):
    def __init__(self, name: str, body: BlockStatement, line: int) -> None:
        super().__init__(StatementType.FUNCTION_DEFINITION, line)
        self.name = name
        self.body = body

class Program:
    def __init__(self, body: list[Statement]):
        self.body = body

    def get_body(self) -> list[Statement]:
        return self.body