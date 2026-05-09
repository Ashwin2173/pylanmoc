FILE_EXTENSION = ".lm"
MAJOR_VERSION = 1
MINOR_VERSION = 0

TOKEN_GRAMMAR = r"""
(?P<COMMENT>//[^\n]*)                                     # single-line comment
| (?P<K_FUNCTION>\bfunction\b)                            # function keyword
| (?P<K_RETURN>\breturn\b)                                # return keyword
| (?P<OPEN_BRACE>\{)                                      # open brace operator
| (?P<CLOSE_BRACE>\})                                     # close brace operator
| (?P<OPEN_PARAM>\()                                      # open param operator
| (?P<CLOSE_PARAM>\))                                     # close param operator
| (?P<SEMI_COLON>\;)                                      # semicolon operator
| (?P<IDENTIFIER>[A-Za-z_]\w*)                            # identifiers and keywords
| (?P<FLOAT>\d+\.\d+)                                     # float numbers
| (?P<INTEGER>\d+)                                        # integer numbers
| (?P<STRING>"(?:\\.|[^"\\])*")                           # double-quoted strings with escape support
| (?P<NEWLINE>\n)                                         # new line
"""