from utils.enums import StatementType

FILE_EXTENSION = ".lm"
COMPILE_EXTENSION = ".lmc"
MAGIC = 2273
MAJOR_VERSION = 1
MINOR_VERSION = 0

TOKEN_GRAMMAR = r"""
(?P<COMMENT>//[^\n]*)                                     # single-line comment
| (?P<K_FUNCTION>\bfunction\b)                            # function keyword
| (?P<K_RETURN>\breturn\b)                                # return keyword
| (?P<K_VAR>\bvar\b)                                      # variable declaration
| (?P<OPEN_BRACE>\{)                                      # open brace operator
| (?P<CLOSE_BRACE>\})                                     # close brace operator
| (?P<OPEN_PARAM>\()                                      # open param operator
| (?P<CLOSE_PARAM>\))                                     # close param operator
| (?P<SEMI_COLON>\;)                                      # semicolon operator
| (?P<K_TRUE>\btrue\b)                                    # boolean true
| (?P<K_FALSE>\bfalse\b)                                  # boolean false
| (?P<K_AND>\band\b)                                      # logical and
| (?P<K_OR>\bor\b)                                        # logical or
| (?P<K_NOT>\bnot\b)                                      # logical not
| (?P<K_IF>\bif\b)                                        # if keyword 
| (?P<K_ELSE>\belse\b)                                    # else keyword 
| (?P<K_NULL>\bnull\b)                                    # null keyword 
| (?P<EQUAL_EQUAL>==)                                     # equal
| (?P<ASSIGN>=)                                           # assignment (after ==)
| (?P<COMMA>,)                                            # comma 
| (?P<BANG>!=)                                            # not equal (bang)
| (?P<LESSER_EQUALS><=)                                   # lesser or equal
| (?P<GREATER_EQUALS>>=)                                  # greater or equal
| (?P<LESSER><)                                           # lesser than
| (?P<GREATER>>)                                          # greater than
| (?P<PLUS>\+)                                            # plus
| (?P<MINUS>-)                                            # minus
| (?P<STAR>\*)                                            # multiply
| (?P<SLASH>/)                                            # divide
| (?P<IDENTIFIER>[A-Za-z_]\w*)                            # identifiers and keywords
| (?P<FLOAT>\d+\.\d+)                                     # float numbers
| (?P<INTEGER>\d+)                                        # integer numbers
| (?P<STRING>"(?:\\.|[^"\\])*")                           # double-quoted strings with escape support
| (?P<NEWLINE>\n)                                         # new line
"""

UNA_MINUS = 1
UNA_BANG = 2

BIN_OP_LOOKUP = {
    StatementType.BINARY_ADD: 1,
    StatementType.BINARY_SUB: 2,
    StatementType.BINARY_MUL: 3,
    StatementType.BINARY_DIV: 4, # todo: Add mod (5)
    StatementType.BINARY_EQUAL_EQUAL: 6,
    StatementType.BINARY_BANG_EQUAL: 7,
    StatementType.BINARY_GREATER_EQUALS: 8,
    StatementType.BINARY_GREATER: 9,
    StatementType.BINARY_LESSER_EQUALS: 10,
    StatementType.BINARY_AND: 12,
    StatementType.BINARY_LESSER: 11,
    StatementType.BINARY_OR: 13
}

BUILT_IN_METHODS = {
    "print",
    "input",
    "len",
    "time"
}