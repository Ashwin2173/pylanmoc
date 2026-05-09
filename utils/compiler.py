import re

from utils.models import (
    BinaryExpression,
    BlockStatement,
    BooleanLiteral,
    ExpressionStatement,
    FloatLiteral,
    FunctionStatement,
    Identifier,
    Integer,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
    UnaryExpression,
    Word,
)
from utils.constants import TOKEN_GRAMMAR
from utils.enums import StatementType, TokenType
from utils.exceptions import LanmoSyntaxError


class Compiler:
    def __init__(self, source: str) -> None:
        self.source = source
        self._tokens: list[Word] = self.__tokenize()
        self.__pos: int = 0
        self.tokens = self._tokens

    def compile(self) -> None:
        program = self.__scan_program()
        print(program)

    def __scan_program(self) -> Program:
        body = self.__scan_global_statements()
        return Program(body=body)

    def __scan_global_statements(self) -> list[Statement]:
        global_statements: list[Statement] = list()
        while True:
            token = self.__peek()
            if token.get_type() == TokenType.K_EOF:
                return global_statements
            if token.get_type() == TokenType.K_FUNCTION:
                self.__next()
                global_statements.append(self.__scan_function_definition())
            else:
                raise LanmoSyntaxError(token, "Invalid Syntax")

    def __scan_function_definition(self) -> FunctionStatement:
        name = self.__next_required("Expected function name after 'function'")
        expect_token(self.__next_required("Expected '(' after function name"), TokenType.OPEN_PARAM)
        expect_token(self.__next_required("Expected ')' after function parameters"), TokenType.CLOSE_PARAM)
        return FunctionStatement(
            name=name.get_raw(),
            body=self.__scan_block_statement(),
            line=name.get_line()
        )

    def __scan_block_statement(self) -> BlockStatement:
        open_brace = self.__next_required("Expected '{' at start of block")
        expect_token(open_brace, TokenType.OPEN_BRACE)
        body: list[Statement] = list()
        while True:
            token = self.__peek()
            if token.get_type() == TokenType.CLOSE_BRACE:
                self.__next()
                return BlockStatement(
                    body=body,
                    line=open_brace.get_line()
                )
            self.__next()
            body.append(self.__scan_local_statement(token))

    def __scan_local_statement(self, token: Word) -> Statement:
        if token.get_type() == TokenType.K_RETURN:
            return self.__scan_return_statement(token)
        raise LanmoSyntaxError(token, "Invalid Syntax")

    def __scan_return_statement(self, token: Word) -> ReturnStatement:
        next_token = self.__next_required("Expected ';' at end of statement")
        if next_token.get_type() == TokenType.SEMI_COLON:
            return ReturnStatement(
                expression=None,
                line=token.get_line()
            )
        expression = self.__scan_expression()
        expect_token(self.__next_required("Expected ';' after return expression"), TokenType.SEMI_COLON)
        return ReturnStatement(
            expression=expression,
            line=token.get_line()
        )

    def __scan_expression(self) -> ExpressionStatement:
        self.__pos -= 1
        return self.__parse_logical_or()

    def __parse_logical_or(self) -> ExpressionStatement:
        left = self.__parse_logical_and()
        while self.__match(TokenType.K_OR):
            token = self.__next()
            right = self.__parse_logical_and()
            left = BinaryExpression(left, right, StatementType.BINARY_PIPE_PIPE, token.get_line())
        return left

    def __parse_logical_and(self) -> ExpressionStatement:
        left = self.__parse_equality()
        while self.__match(TokenType.K_AND):
            token = self.__next()
            right = self.__parse_equality()
            left = BinaryExpression(left, right, StatementType.BINARY_AMP_AMP, token.get_line())
        return left

    def __parse_equality(self) -> ExpressionStatement:
        left = self.__parse_comparison()
        while self.__match(TokenType.EQUAL_EQUAL, TokenType.BANG):
            token = self.__next()
            stmt_type = {
                TokenType.EQUAL_EQUAL: StatementType.BINARY_EQUAL_EQUAL,
                TokenType.BANG:        StatementType.BINARY_BANG_EQUAL
            }[token.get_type()]
            right = self.__parse_comparison()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __parse_comparison(self) -> ExpressionStatement:
        left = self.__parse_term()
        while self.__match(TokenType.LESSER, TokenType.LESSER_EQUALS,
            TokenType.GREATER, TokenType.GREATER_EQUALS):
            token = self.__next()
            stmt_type = {
                TokenType.LESSER:         StatementType.BINARY_LESSER,
                TokenType.LESSER_EQUALS:  StatementType.BINARY_LESSER_EQUALS,
                TokenType.GREATER:        StatementType.BINARY_GREATER,
                TokenType.GREATER_EQUALS: StatementType.BINARY_GREATER_EQUALS
            }[token.get_type()]
            right = self.__parse_term()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __parse_term(self) -> ExpressionStatement:
        left = self.__parse_factor()
        while self.__match(TokenType.PLUS, TokenType.MINUS):
            token = self.__next()
            stmt_type = {
                TokenType.PLUS:  StatementType.BINARY_ADD,
                TokenType.MINUS: StatementType.BINARY_SUB
            }[token.get_type()]
            right = self.__parse_factor()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __parse_factor(self) -> ExpressionStatement:
        left = self.__parse_unary()
        while self.__match(TokenType.STAR, TokenType.SLASH):
            token = self.__next()
            stmt_type = {
                TokenType.STAR:  StatementType.BINARY_MUL,
                TokenType.SLASH: StatementType.BINARY_DIV
            }[token.get_type()]
            right = self.__parse_unary()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __parse_unary(self) -> ExpressionStatement:
        if self.__match(TokenType.K_NOT, TokenType.MINUS, TokenType.PLUS):
            token = self.__next()
            right = self.__parse_unary()
            if token.get_type() == TokenType.K_NOT:
                return UnaryExpression(right, StatementType.UNARY_BANG, token.get_line())
            if token.get_type() == TokenType.MINUS:
                return UnaryExpression(right, StatementType.UNARY_MINUS, token.get_line())
            return UnaryExpression(right, StatementType.UNARY_PLUS, token.get_line())
        return self.__parse_primary()

    def __parse_primary(self) -> ExpressionStatement:
        token = self.__next()
        line = token.get_line()
        token_type = token.get_type()
        if token_type == TokenType.INTEGER:
            return Integer(token, line)
        if token_type == TokenType.FLOAT:
            return FloatLiteral(token, line)
        if token_type == TokenType.STRING:
            return StringLiteral(token, line)
        if token_type == TokenType.K_TRUE or token_type == TokenType.K_FALSE:
            return BooleanLiteral(token, line)
        if token_type == TokenType.IDENTIFIER:
            return Identifier(token, line)
        if token_type == TokenType.OPEN_PARAM:
            inner = self.__parse_logical_or()
            expect_token(self.__next(), TokenType.CLOSE_PARAM)
            return inner
        raise LanmoSyntaxError(token, "Invalid Syntax")

    def __match(self, *types: TokenType) -> bool:
        return self.__peek().get_type() in types

    def __peek(self) -> Word:
        if self.__pos >= len(self._tokens):
            raise LanmoSyntaxError(None, "Invalid source file")
        return self._tokens[self.__pos]

    def __next(self) -> Word:
        token = self.__peek()
        self.__pos += 1
        return token

    def __tokenize(self) -> list[Word]:
        tokens: list[Word] = []
        line = 1
        compiled_grammar = re.compile(TOKEN_GRAMMAR, re.VERBOSE)
        for item in compiled_grammar.finditer(self.source):
            token_type = TokenType[item.lastgroup]
            if token_type == TokenType.NEWLINE:
                line += 1
            elif token_type == TokenType.COMMENT:
                continue
            else:
                raw = item.group()
                token_span = (item.start(), item.end())
                tokens.append(Word(raw, token_type, line, token_span))
        tokens.append(Word("EOF", TokenType.K_EOF, 0, (0, 0)))
        return tokens

    def __next_required(self, message: str) -> Word:
        if self.__pos >= len(self._tokens):
            raise LanmoSyntaxError(None, message)
        return self.__next()


def expect_token(token: Word, token_type: TokenType) -> None:
    if token.get_type() != token_type:
        raise LanmoSyntaxError(token, f"Expected {token_type.name}, but got {token.get_type().value}")
