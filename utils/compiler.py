import re

from utils.models import (
    Word,
    Integer,
    Program,
    Statement,
    Identifier,
    IfStatement,
    FloatLiteral,
    StringLiteral,
    BlockStatement,
    BooleanLiteral,
    ReturnStatement,
    UnaryExpression,
    BinaryExpression,
    FunctionStatement,
    ExpressionStatement,
    AssignmentStatement,
    VariableDeclaration,
)
from utils.constants import TOKEN_GRAMMAR
from utils.enums import StatementType, TokenType
from utils.exceptions import LanmoSyntaxError


class Compiler:
    def __init__(self, source: str) -> None:
        self.source = source
        self.__tokens: list[Word] = self.__tokenize()
        self.__pos: int = 0
        self.tokens = self.__tokens

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
        if token.get_type() == TokenType.K_VAR:
            return self.__scan_var_statement(token)
        if token.get_type() == TokenType.K_IF:
            return self.__scan_if_statement(token)
        if token.get_type() == TokenType.OPEN_BRACE:
            self.__pos -= 1
            return self.__scan_block_statement()
        return self.__scan_expression_statement()

    def __scan_expression_statement(self) -> ExpressionStatement:
        expression = self.__scan_raw_expression()
        expect_token(self.__next(), TokenType.SEMI_COLON)
        return expression

    def __scan_return_statement(self, token: Word) -> ReturnStatement:
        next_token = self.__next_required("Expected ';' or expression after 'return'")
        if next_token.get_type() == TokenType.SEMI_COLON:
            return ReturnStatement(
                expression=None,
                line=token.get_line()
            )
        expression = self.__scan_raw_expression()
        expect_token(self.__next_required("Expected ';' after return expression"), TokenType.SEMI_COLON)
        return ReturnStatement(
            expression=expression,
            line=token.get_line()
        )

    def __scan_if_statement(self, token: Word) -> IfStatement:
        self.__next_required("Expected expression after 'if'")
        test_expression = self.__scan_raw_expression()
        consequent = self.__scan_local_statement(self.__next())
        alternate = None
        if self.__peek().get_type() == TokenType.K_ELSE:
            self.__next_required("Expected statement after 'else'")
            alternate = self.__scan_local_statement(self.__next())
        return IfStatement(
            test=test_expression,
            consequent=consequent,
            alternate=alternate,
            line=token.get_line()
        )

    def __scan_var_statement(self, var_token: Word) -> VariableDeclaration:
        name_token = self.__next_required("Expected variable name after 'var'")
        expect_token(name_token, TokenType.IDENTIFIER)
        assign_token = self.__next_required("Expected '=' after variable name")
        expect_token(assign_token, TokenType.ASSIGN)
        initializer = self.__scan_logical_or()
        expect_token(self.__next_required("Expected ';' after variable declaration"), TokenType.SEMI_COLON)
        return VariableDeclaration(
            name=name_token.get_raw(),
            initializer=initializer,
            line=var_token.get_line()
        )

    def __scan_assignment_statement(self, name_token: Word) -> AssignmentStatement:
        assign_token = self.__next_required("Expected '=' in assignment")
        expect_token(assign_token, TokenType.ASSIGN)
        value = self.__scan_logical_or()
        return AssignmentStatement(
            name=name_token.get_raw(),
            value=value,
            line=name_token.get_line()
        )

    def __scan_raw_expression(self) -> ExpressionStatement:
        self.__pos -= 1
        return self.__scan_logical_or()

    def __scan_logical_or(self) -> ExpressionStatement:
        left = self.__scan_logical_and()
        while self.__match(TokenType.K_OR):
            token = self.__next()
            right = self.__scan_logical_and()
            left = BinaryExpression(left, right, StatementType.BINARY_PIPE_PIPE, token.get_line())
        return left

    def __scan_logical_and(self) -> ExpressionStatement:
        left = self.__scan_equality()
        while self.__match(TokenType.K_AND):
            token = self.__next()
            right = self.__scan_equality()
            left = BinaryExpression(left, right, StatementType.BINARY_AMP_AMP, token.get_line())
        return left

    def __scan_equality(self) -> ExpressionStatement:
        left = self.__scan_comparison()
        while self.__match(TokenType.EQUAL_EQUAL, TokenType.BANG):
            token = self.__next()
            stmt_type = {
                TokenType.EQUAL_EQUAL: StatementType.BINARY_EQUAL_EQUAL,
                TokenType.BANG:        StatementType.BINARY_BANG_EQUAL
            }[token.get_type()]
            right = self.__scan_comparison()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __scan_comparison(self) -> ExpressionStatement:
        left = self.__scan_term()
        while self.__match(TokenType.LESSER, TokenType.LESSER_EQUALS,
            TokenType.GREATER, TokenType.GREATER_EQUALS):
            token = self.__next()
            stmt_type = {
                TokenType.LESSER:         StatementType.BINARY_LESSER,
                TokenType.LESSER_EQUALS:  StatementType.BINARY_LESSER_EQUALS,
                TokenType.GREATER:        StatementType.BINARY_GREATER,
                TokenType.GREATER_EQUALS: StatementType.BINARY_GREATER_EQUALS
            }[token.get_type()]
            right = self.__scan_term()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __scan_term(self) -> ExpressionStatement:
        left = self.__scan_factor()
        while self.__match(TokenType.PLUS, TokenType.MINUS):
            token = self.__next()
            stmt_type = {
                TokenType.PLUS:  StatementType.BINARY_ADD,
                TokenType.MINUS: StatementType.BINARY_SUB
            }[token.get_type()]
            right = self.__scan_factor()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __scan_factor(self) -> ExpressionStatement:
        left = self.__scan_unary()
        while self.__match(TokenType.STAR, TokenType.SLASH):
            token = self.__next()
            stmt_type = {
                TokenType.STAR:  StatementType.BINARY_MUL,
                TokenType.SLASH: StatementType.BINARY_DIV
            }[token.get_type()]
            right = self.__scan_unary()
            left = BinaryExpression(left, right, stmt_type, token.get_line())
        return left

    def __scan_unary(self) -> ExpressionStatement:
        if self.__match(TokenType.K_NOT, TokenType.MINUS, TokenType.PLUS):
            token = self.__next()
            right = self.__scan_unary()
            if token.get_type() == TokenType.K_NOT:
                return UnaryExpression(right, StatementType.UNARY_BANG, token.get_line())
            if token.get_type() == TokenType.MINUS:
                return UnaryExpression(right, StatementType.UNARY_MINUS, token.get_line())
            return UnaryExpression(right, StatementType.UNARY_PLUS, token.get_line())
        return self.__scan_primary()

    def __scan_primary(self) -> ExpressionStatement:
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
            return self.__scan_identifier(token, line)
        if token_type == TokenType.OPEN_PARAM:
            inner = self.__scan_logical_or()
            expect_token(self.__next(), TokenType.CLOSE_PARAM)
            return inner
        raise LanmoSyntaxError(token, "Invalid Syntax")

    def __scan_identifier(self, token: Word, line: int) -> ExpressionStatement:
        next_token = self.__peek()
        if next_token.get_type() == TokenType.ASSIGN:
            return self.__scan_assignment_statement(token)
        expect_token(token, TokenType.IDENTIFIER)
        return Identifier(token, line)

    def __match(self, *types: TokenType) -> bool:
        return self.__peek().get_type() in types

    def __peek(self, offset: int=0) -> Word:
        if self.__pos >= len(self.__tokens) + offset:
            raise LanmoSyntaxError(None, "Invalid source file")
        return self.__tokens[self.__pos + offset]

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
        if self.__pos >= len(self.__tokens):
            raise LanmoSyntaxError(None, message)
        return self.__next()


def expect_token(token: Word, token_type: TokenType) -> None:
    if token.get_type() != token_type:
        raise LanmoSyntaxError(token, f"Expected {token_type.name}, but got {token.get_type().value}")
