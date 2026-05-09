from enum import Enum, auto

class TokenType(Enum):
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"

    OPEN_BRACE = "OPEN_BRACE"
    CLOSE_BRACE = "CLOSE_BRACE"
    OPEN_PARAM = "OPEN_PARAM"
    CLOSE_PARAM = "CLOSE_PARAM"
    SEMI_COLON = "SEMI_COLON"

    IDENTIFIER = "IDENTIFIER"
    FLOAT = "FLOAT"
    INTEGER = "INTEGER"
    STRING = "STRING"

    K_FUNCTION = "function"
    K_RETURN = "return"
    K_EOF = "eof"


class StatementType(Enum):
    FUNCTION_DEFINITION = auto()
    BLOCK_STATEMENT = auto()
    RETURN_STATEMENT = auto()