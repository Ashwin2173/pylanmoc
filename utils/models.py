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
    
class ExpressionStatement(Statement):
    def __init__(self, s_type: StatementType, line: int) -> None:
        super().__init__(s_type, line)

class CallExpression(ExpressionStatement):
    def __init__(self, callee: ExpressionStatement, arguments: list[ExpressionStatement], line: int):
        super().__init__(StatementType.CALL_EXPRESSION, line)
        self.callee = callee
        self.arguments = arguments

class IntegerLiteral(ExpressionStatement):
    def __init__(self, token: Word, line: int):
        super().__init__(StatementType.INTEGER, line)
        self.token = token

class FloatLiteral(ExpressionStatement):
    def __init__(self, token: Word, line: int):
        super().__init__(StatementType.FLOAT, line)
        self.token = token

class StringLiteral(ExpressionStatement):
    def __init__(self, token: Word, line: int):
        super().__init__(StatementType.STRING, line)
        self.token = token

class NullLiteral(ExpressionStatement):
    def __init__(self, token: Word, line: int):
        super().__init__(StatementType.NULL, line)
        self.token = token

class BooleanLiteral(ExpressionStatement):
    def __init__(self, token: Word, line: int):
        super().__init__(StatementType.BOOLEAN, line)
        self.token = token

class Identifier(ExpressionStatement):
    def __init__(self, token: Word, line: int):
        super().__init__(StatementType.IDENTIFIER, line)
        self.token = token

class UnaryExpression(ExpressionStatement):
    def __init__(self, value: ExpressionStatement, s_type: StatementType, line: int) -> None:
        super().__init__(s_type, line)
        self.value = value

class BinaryExpression(ExpressionStatement):
    def __init__(self, left: ExpressionStatement, right: ExpressionStatement, s_type: StatementType, line: int) -> None:
        super().__init__(s_type, line)
        self.left = left
        self.right = right

class ReturnStatement(Statement):
    def __init__(self, expression: ExpressionStatement | None, line: int) -> None:
        super().__init__(StatementType.RETURN_STATEMENT, line)
        self.expression = expression

class VariableDeclaration(Statement):
    def __init__(self, name: str, initializer: ExpressionStatement, line: int) -> None:
        super().__init__(StatementType.VARIABLE_DECLARATION, line)
        self.name = name
        self.initializer = initializer

class AssignmentStatement(ExpressionStatement):
    def __init__(self, name: str, value: ExpressionStatement, line: int) -> None:
        super().__init__(StatementType.ASSIGNMENT_STATEMENT, line)
        self.name = name
        self.value = value

class BlockStatement(Statement):
    def __init__(self, body: list[Statement], line: int) -> None:
        super().__init__(StatementType.BLOCK_STATEMENT, line)
        self.body = body

class IfStatement(Statement):
    def __init__(self, test: ExpressionStatement, consequent: Statement, alternate: Statement, line: int) -> None:
        super().__init__(StatementType.IF_STATEMENT, line)
        self.test = test
        self.consequent = consequent
        self.alternate = alternate

class FunctionStatement(Statement):
    def __init__(self, name: Word, body: BlockStatement, line: int) -> None:
        super().__init__(StatementType.FUNCTION_DEFINITION, line)
        self.name = name
        self.body = body

class Program:
    def __init__(self, body: list[Statement], frame_names: set[str]):
        self.body = body
        self.frame_names = frame_names

    def get_body(self) -> list[Statement]:
        return self.body