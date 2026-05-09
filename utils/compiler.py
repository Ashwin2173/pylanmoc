import re

from utils.models import *
from utils.constants import TOKEN_GRAMMAR
from utils.exceptions import LanmoSyntaxError

class Compiler:
    def __init__(self, program_file: str) -> None:
        self.program_file = program_file
        self.tokens = self.__token_iter()

    def compile(self) -> None:
        try:
            program = self.__scan_program()
            print(program)
        except StopIteration:
            return None

    def __scan_program(self) -> Program:
        body = self.__scan_global_statements()
        return Program(body = body)

    def __scan_global_statements(self) -> list[Statement] | None:
        global_statements: list[Statement] = list()
        for token in self.tokens:
            if token.get_type() == TokenType.K_FUNCTION:
                global_statements.append(self.__scan_function_definition())
            elif token.get_type() == TokenType.K_EOF:
                return global_statements
            else:
                raise LanmoSyntaxError(token, "Invalid Syntax")

    def __scan_function_definition(self) -> FunctionStatement:
        name = next(self.tokens)
        expect_token(next(self.tokens), TokenType.OPEN_PARAM)
        expect_token(next(self.tokens), TokenType.CLOSE_PARAM)
        return FunctionStatement(
            name = name.get_raw(),
            body = self.__scan_block_statement(),
            line = name.get_line()
        )

    def __scan_block_statement(self) -> BlockStatement | None:
        open_brace = next(self.tokens)
        expect_token(open_brace, TokenType.OPEN_BRACE)
        body: list[Statement] = list()
        for token in self.tokens:
            if token.get_type() == TokenType.CLOSE_BRACE:
                return BlockStatement(
                    body = body,
                    line = open_brace.get_line()
                )
            body.append(self.__scan_local_statement(token))

    def __scan_local_statement(self, token: Word) -> Statement:
        if token.get_type() == TokenType.K_RETURN:
            return self.__scan_return_statement(token)
        else:
            raise LanmoSyntaxError(token, "Invalid Syntax")

    def __scan_return_statement(self, token: Word) -> ReturnStatement:
        expect_token(next(self.tokens), TokenType.SEMI_COLON)
        return ReturnStatement(
            expression = None,
            line = token.get_line()
        )

    def __token_iter(self):
        for token in self.__tokenize():
            yield token

    def __tokenize(self) -> list[Word]:
        tokens = list()
        line = 1
        compiled_grammar = re.compile(TOKEN_GRAMMAR, re.VERBOSE)
        for item in compiled_grammar.finditer(self.program_file):
            token_type = TokenType[item.lastgroup]
            if token_type == TokenType.NEWLINE:
                line += 1
            elif token_type == TokenType.COMMENT:
                continue
            else:
                raw = item.group()
                token_span = (item.start(), item.end())
                tokens.append(Word(raw, token_type, line, token_span))
        if len(tokens) != 0:
            tokens.append(Word('EOF', TokenType.K_EOF, 0, (0, 0)))
        return tokens

def expect_token(token: Word, token_type: TokenType) -> None:
    if token.get_type() != token_type:
        raise LanmoSyntaxError(token, f"Expected {token_type.name}, but got {token.get_type().value}")