from enum import Enum, auto

class TokenType(Enum):
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"

    OPEN_BRACE = "OPEN_BRACE"
    CLOSE_BRACE = "CLOSE_BRACE"
    OPEN_PARAM = "OPEN_PARAM"
    CLOSE_PARAM = "CLOSE_PARAM"
    OPEN_SQUARE = "OPEN_SQUARE"
    CLOSE_SQUARE = "CLOSE_SQUARE"
    COMMA = "COMMA"
    SEMI_COLON = "SEMI_COLON"
    DOT = "DOT"

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
    K_WHILE = "while"
    K_ELSE = "else"
    K_NULL = "null"
    K_STRUCT = "struct"

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
    STRUCT_DEFINITION = auto()
    BLOCK_STATEMENT = auto()
    RETURN_STATEMENT = auto()
    EXPRESSION_STATEMENT = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()
    STRUCT = auto()

    UNARY_MINUS = auto()
    UNARY_BANG = auto()

    BINARY_ASSIGN = auto()
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
    INDEX_EXPRESSION = auto()
    SEQUENCE_EXPRESSION = auto()
    MEMBER_EXPRESSION = auto()

    VARIABLE_DECLARATION = auto()
    ASSIGNMENT_STATEMENT = auto()
    IF_STATEMENT = auto()
    WHILE_STATEMENT = auto()


class DataType(Enum):
    INTEGER    = auto()
    STRING     = auto()
    VARIABLE   = auto()
    FUNCTION   = auto()
    NONE       = auto()
    BOOLEAN    = auto()


class OpCodeType(Enum):
    PUSH          = auto()
    POP           = auto()
    BIN_OP        = auto()
    WRITE         = auto()
    CALL          = auto()
    HALT          = auto()
    RETURN        = auto()
    JUMP          = auto()
    JUMP_IF_FALSE = auto()
    DUP           = auto()
    STORE         = auto()
    LOAD          = auto()
    MAKE_LIST     = auto()
    GET_INDEX     = auto()
    SET_INDEX     = auto()
    UNARY_OP      = auto()
    NEW_OBJ    = auto()
    GET_FIELD = auto()
    SET_FIELD = auto()
