import re
from typing import cast

from utils.models import (
    Word,
    Program,
    Statement,
    Identifier,
    IfStatement,
    NullLiteral,
    FloatLiteral,
    StringLiteral,
    BlockStatement,
    BooleanLiteral,
    IntegerLiteral,
    CallExpression,
    ReturnStatement,
    UnaryExpression,
    BinaryExpression,
    FunctionStatement,
    ExpressionStatement,
    VariableDeclaration,
)
from utils.byte_generator import ByteCodeGenerator
from utils.constants import TOKEN_GRAMMAR, BUILT_IN_METHODS
from utils.enums import StatementType, TokenType
from utils.exceptions import LanmoSyntaxError

class Compiler:
    def __init__(self, source: str) -> None:
        self.source = source
        self.__tokens: list[Word] = self.__tokenize()
        self.frame_names = set()
        self.__pos: int = 0

    def compile(self) -> bytearray:
        program = self.__scan_program()
        bg = ByteCodeGenerator(program)
        return bg.pack_byte_code()

    def __scan_program(self) -> Program:
        body = self.__scan_global_statements()
        return Program(body=body, frame_names=self.frame_names)

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
        self.frame_names.add(name.get_raw())
        expect_token(self.__next_required("Expected '(' after function name"), TokenType.OPEN_PARAM)
        expect_token(self.__next_required("Expected ')' after function parameters"), TokenType.CLOSE_PARAM)
        return FunctionStatement(
            name=name,
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
            body.append(self.__scan_local_statement(token))

    def __scan_local_statement(self, token: Word) -> Statement:
        if token.get_type() == TokenType.K_RETURN:
            self.__next()
            return self.__scan_return_statement(token)
        if token.get_type() == TokenType.K_VAR:
            self.__next()
            return self.__scan_var_statement(token)
        if token.get_type() == TokenType.K_IF:
            self.__next()
            return self.__scan_if_statement(token)
        if token.get_type() == TokenType.OPEN_BRACE:
            return self.__scan_block_statement()
        return self.__scan_expression_statement()

    def __scan_expression_statement(self) -> ExpressionStatement:
        expression = self.__scan_expression()
        expect_token(self.__next(), TokenType.SEMI_COLON)
        return expression

    def __scan_return_statement(self, token: Word) -> ReturnStatement:
        next_token = self.__peek()
        if next_token.get_type() == TokenType.SEMI_COLON:
            self.__next()
            return ReturnStatement(
                expression=NullLiteral(next_token, next_token.get_line()),
                line=token.get_line()
            )
        expression = self.__scan_expression()
        expect_token(self.__next_required("Expected ';' after return expression"), TokenType.SEMI_COLON)
        return ReturnStatement(
            expression=expression,
            line=token.get_line()
        )

    def __scan_if_statement(self, token: Word) -> IfStatement:
        next_token = self.__next_required("Expected expression after 'if'")
        expect_token(next_token, TokenType.OPEN_PARAM)
        test_expression = self.__scan_expression()
        expect_token(self.__peek(offset=-1), TokenType.CLOSE_PARAM)
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
        initializer = self.__scan_expression()
        expect_token(self.__next_required("Expected ';' after variable declaration"), TokenType.SEMI_COLON)
        return VariableDeclaration(
            name=name_token,
            initializer=initializer,
            line=var_token.get_line()
        )

    def __scan_expression(self) -> ExpressionStatement:
        return self.__scan_assignment()

    def __scan_assignment(self) -> ExpressionStatement:
        left = self.__scan_logical_or()
        if self.__match(TokenType.ASSIGN):
            token = self.__next()
            right = self.__scan_assignment()
            if not is_assignable(left):
                raise LanmoSyntaxError(token, "Illegal assignment expression")
            left = BinaryExpression(left, right, StatementType.BINARY_ASSIGN, token.get_line())
        return left

    def __scan_logical_or(self) -> ExpressionStatement:
        left = self.__scan_logical_and()
        while self.__match(TokenType.K_OR):
            token = self.__next()
            right = self.__scan_logical_and()
            left = BinaryExpression(left, right, StatementType.BINARY_OR, token.get_line())
        return left

    def __scan_logical_and(self) -> ExpressionStatement:
        left = self.__scan_equality()
        while self.__match(TokenType.K_AND):
            token = self.__next()
            right = self.__scan_equality()
            left = BinaryExpression(left, right, StatementType.BINARY_AND, token.get_line())
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
        return self.__scan_postfix()

    def __finish_call_expression(self, expr: ExpressionStatement) -> CallExpression:
        token = self.__next_required("Expected '(' in function call")
        arguments = list()
        if self.__match(TokenType.CLOSE_PARAM):
            self.__next()
        else:
            while True:
                arguments.append(self.__scan_expression())
                if self.__peek().get_type() == TokenType.COMMA:
                    self.__next()
                    continue
                expect_token(self.__next_required("Expected ')' after arguments"), TokenType.CLOSE_PARAM)
                break
        return CallExpression(
            callee=expr,
            arguments=arguments,
            line=token.get_line()
        )

    def __scan_postfix(self) -> ExpressionStatement:
        expr = self.__scan_primary()
        while True:
            if self.__match(TokenType.OPEN_PARAM):
                expr = self.__finish_call_expression(expr)
            else:
                break
        return expr

    def __scan_primary(self) -> ExpressionStatement:
        token = self.__next()
        line = token.get_line()
        token_type = token.get_type()
        if token_type == TokenType.INTEGER:
            return IntegerLiteral(token, line)
        if token_type == TokenType.FLOAT:
            return FloatLiteral(token, line)
        if token_type == TokenType.STRING:
            return StringLiteral(token, line)
        if token_type == TokenType.K_NULL:
            return NullLiteral(token, line)
        if token_type == TokenType.K_TRUE or token_type == TokenType.K_FALSE:
            return BooleanLiteral(token, line)
        if token_type == TokenType.IDENTIFIER:
            return self.__scan_identifier(token, line)
        print(f"[ LOG ] {token}")
        raise LanmoSyntaxError(token, "Invalid Syntax")

    def __scan_identifier(self, token: Word, line: int) -> Identifier:
        if token.get_raw() in BUILT_IN_METHODS:
            self.frame_names.add(token.get_raw())
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
                tokens.append(Word(raw, cast(TokenType, token_type), line, token_span))
        tokens.append(Word("EOF", TokenType.K_EOF, 0, (0, 0)))
        return tokens

    def __next_required(self, message: str) -> Word:
        if self.__pos >= len(self.__tokens):
            raise LanmoSyntaxError(None, message)
        return self.__next()

def expect_token(token: Word, token_type: TokenType) -> None:
    if token.get_type() != token_type:
        raise LanmoSyntaxError(token, f"Expected {token_type.name}, but got {token.get_type().value}")

def is_assignable(expr: ExpressionStatement) -> bool:
    return expr.get_type() in { StatementType.IDENTIFIER }
