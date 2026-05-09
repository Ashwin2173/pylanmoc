FILE_EXTENSION = ".lm"
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
| (?P<EQUAL_EQUAL>==)                                     # equal
| (?P<ASSIGN>=)                                           # assignment (after ==)
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
