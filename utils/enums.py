from enum import Enum, auto

class TokenType(Enum):
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"

    OPEN_BRACE = "OPEN_BRACE"
    CLOSE_BRACE = "CLOSE_BRACE"
    OPEN_PARAM = "OPEN_PARAM"
    CLOSE_PARAM = "CLOSE_PARAM"
    COMMA = "COMMA"
    SEMI_COLON = "SEMI_COLON"

    IDENTIFIER = "IDENTIFIER"
    FLOAT = "FLOAT"
    INTEGER = "INTEGER"
    STRING = "STRING"

    K_FUNCTION = "function"
    K_RETURN = "return"
    K_VAR = "var"
    K_TRUE = "true"
    K_FALSE = "false"
    K_AND = "and"
    K_OR = "or"
    K_NOT = "not"
    K_IF = "if"
    K_ELSE = "else"

    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    EQUAL_EQUAL = "EQ"
    ASSIGN = "ASSIGN"
    BANG = "BANG"
    LESSER = "LESSER"
    LESSER_EQUALS = "LESSER_EQUALS"
    GREATER = "GREATER"
    GREATER_EQUALS = "GREATER_EQUALS"

    K_EOF = "eof"


class StatementType(Enum):
    FUNCTION_DEFINITION = auto()
    BLOCK_STATEMENT = auto()
    RETURN_STATEMENT = auto()
    EXPRESSION_STATEMENT = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()

    UNARY_PLUS = auto()
    UNARY_MINUS = auto()
    UNARY_BANG = auto()

    BINARY_OR = auto()
    BINARY_AND = auto()
    BINARY_EQUAL_EQUAL = auto()
    BINARY_BANG_EQUAL = auto()
    BINARY_LESSER = auto()
    BINARY_LESSER_EQUALS = auto()
    BINARY_GREATER = auto()
    BINARY_GREATER_EQUALS = auto()
    BINARY_ADD = auto()
    BINARY_SUB = auto()
    BINARY_MUL = auto()
    BINARY_DIV = auto()
    CALL_EXPRESSION = auto()

    VARIABLE_DECLARATION = auto()
    ASSIGNMENT_STATEMENT = auto()
    IF_STATEMENT = auto()
