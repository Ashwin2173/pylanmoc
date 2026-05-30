import struct
from typing import cast

from utils.constants import (
    MAGIC,
    MAJOR_VERSION,
    MINOR_VERSION,
    UNA_OP_LOOKUP,
    BIN_OP_LOOKUP,
    BUILT_IN_METHODS
)
from utils.models import (
    Word,
    Trace,
    Program,
    Statement,
    Identifier,
    NullLiteral,
    IfStatement,
    StringLiteral,
    BooleanLiteral,
    IntegerLiteral,
    WhileStatement,
    CallExpression,
    BlockStatement,
    ReturnStatement,
    IndexExpression,
    BinaryExpression,
    FunctionStatement,
    ExpressionStatement,
    VariableDeclaration,
    SequenceExpression, UnaryExpression
)
from utils.enums import (
    DataType,
    TokenType,
    OpCodeType,
    StatementType
)
from utils.exceptions import LanmoSyntaxError

class ByteCodeGenerator:
    def __init__(self, program: Program) -> None:
        self.program = program

        self.raw_symbols = dict()
        self.global_scope = self.program.frame_names.union(BUILT_IN_METHODS)
        self.function_count = 0

        self.symbol_table = bytearray()
        self.program_code = bytearray()

        self.instructions: Instruction | None = None
        self.stack_trace: StackTrace | None = None

    def pack_byte_code(self) -> bytearray:
        self.__handle_global_statements()
        if len(self.raw_symbols) >= 65534:
            raise LanmoSyntaxError(None, "The file contains too many symbols")
        bc = bytearray()
        bc += struct.pack("<IHH", MAGIC, MAJOR_VERSION, MINOR_VERSION)
        bc += struct.pack("<H", len(self.raw_symbols))
        bc += self.symbol_table
        bc += struct.pack("<H", self.function_count)
        bc += self.program_code
        return bc

    def __handle_global_statements(self) -> None:
        for item in self.program.get_body():
            if item.get_type() == StatementType.FUNCTION_DEFINITION:
                self.__handle_function(cast(FunctionStatement, item))
            else:
                raise NotImplementedError(item.get_type())

    def __handle_function(self, function: FunctionStatement) -> None:
        self.function_count += 1
        self.instructions = Instruction()
        self.stack_trace = StackTrace()

        index = self.__add_constant(DataType.FUNCTION, function.name)
        self.__handle_block(StatementType.FUNCTION_DEFINITION, function.body, function.arguments)
        frame = bytearray()
        frame += struct.pack("<H", index)
        frame += struct.pack("<B", len(function.arguments))
        frame += struct.pack("<I", self.stack_trace.slot_size)
        frame += struct.pack("<H", 255)
        frame += struct.pack("<I", self.instructions.get_count())
        frame += self.instructions.get_raw()
        self.program_code += frame

    def __handle_function_arguments(self, arguments: list[Identifier]) -> None:
        for argument in arguments:
            slot_id = self.stack_trace.create_variable(argument.token)
            self.instructions.push_inst(OpCodeType.STORE, slot_id)

    def __handle_block(self, stmt_type: StatementType, block: BlockStatement, arguments: list[Identifier]=None) -> None:
        self.stack_trace.push(stmt_type, block.get_line())
        if arguments is not None:
            self.__handle_function_arguments(arguments)
        for statement in block.body:
            self.__handle_statement(statement)
        self.stack_trace.pop()

    def __handle_statement(self, statement: Statement) -> None:
        if statement.get_type() == StatementType.RETURN_STATEMENT:
            self.__handle_return(cast(ReturnStatement, statement))
        elif statement.get_type() == StatementType.VARIABLE_DECLARATION:
            self.__handle_variable_declaration(cast(VariableDeclaration, statement))
        elif statement.get_type() == StatementType.IF_STATEMENT:
            self.__handle_if_statement(cast(IfStatement, statement))
        elif statement.get_type() == StatementType.WHILE_STATEMENT:
            self.__handle_while_statement(cast(WhileStatement, statement))
        elif statement.get_type() == StatementType.BLOCK_STATEMENT:
            self.__handle_block(StatementType.BLOCK_STATEMENT, cast(BlockStatement, statement))
        else:
            self.__handle_expression(cast(ExpressionStatement, statement))
            self.instructions.push_inst(OpCodeType.POP)

    def __handle_while_statement(self, stmt: WhileStatement) -> None:
        loop_pointer = self.instructions.get_count()
        self.__handle_expression(stmt.test)
        condition_pointer = self.instructions.push_inst(OpCodeType.JUMP_IF_FALSE) - 1
        self.__handle_statement(stmt.body)
        self.instructions.push_inst(OpCodeType.JUMP, loop_pointer)
        self.instructions.update_inst(condition_pointer, self.instructions.get_count())

    def __handle_if_statement(self, stmt: IfStatement) -> None:
        self.__handle_expression(stmt.test)
        condition_pointer = self.instructions.push_inst(OpCodeType.JUMP_IF_FALSE) - 1
        self.__handle_statement(stmt.consequent)
        self.instructions.update_inst(condition_pointer, self.instructions.get_count())
        if stmt.alternate is not None:
            else_pointer = self.instructions.push_inst(OpCodeType.JUMP) - 1
            self.instructions.update_inst(condition_pointer, self.instructions.get_count())
            self.__handle_statement(stmt.alternate)
            self.instructions.update_inst(else_pointer, self.instructions.get_count())

    def __handle_variable_declaration(self, declaration: VariableDeclaration) -> None:
        name = declaration.name
        if self.__is_function(name):
            raise LanmoSyntaxError(name, f"Identifier '{ name.get_raw() }' is already defined as a function")
        self.__handle_expression(declaration.initializer)
        slot_id = self.stack_trace.create_variable(declaration.name)
        self.instructions.push_inst(OpCodeType.STORE, slot_id)
        self.instructions.push_inst(OpCodeType.POP)

    def __handle_return(self, return_stmt: ReturnStatement) -> None:
        self.__handle_expression(return_stmt.expression)
        self.instructions.push_inst(OpCodeType.RETURN, 0)

    def __handle_expression(self, expr: ExpressionStatement) -> None:
        if expr.get_type() in BIN_OP_LOOKUP:
            bin_exp: BinaryExpression = cast(BinaryExpression, expr)
            self.__handle_expression(bin_exp.left)
            self.__handle_expression(bin_exp.right)
            self.instructions.push_inst(OpCodeType.BIN_OP, BIN_OP_LOOKUP[expr.s_type])
        elif expr.get_type() in UNA_OP_LOOKUP:
            self.__handle_expression(cast(UnaryExpression, expr).value)
            self.instructions.push_inst(OpCodeType.UNARY_OP, UNA_OP_LOOKUP[expr.s_type])
        elif expr.get_type() == StatementType.BINARY_ASSIGN:
            self.__handle_assignment(cast(BinaryExpression, expr))
        elif expr.get_type() == StatementType.CALL_EXPRESSION:
            self.__handle_call_statement(cast(CallExpression, expr))
        elif expr.get_type() == StatementType.INDEX_EXPRESSION:
            self.__handle_index_statement(cast(IndexExpression, expr))
        elif expr.get_type() == StatementType.IDENTIFIER:
            self.__handle_identifier(cast(Identifier, expr))
        elif expr.get_type() == StatementType.SEQUENCE_EXPRESSION:
            self.__handle_sequence(cast(SequenceExpression, expr))
        elif expr.get_type() == StatementType.BOOLEAN:
            self.__push(DataType.BOOLEAN, cast(BooleanLiteral, expr).token)
        elif expr.get_type() == StatementType.INTEGER:
            self.__push(DataType.INTEGER, cast(IntegerLiteral, expr).token)
        elif expr.get_type() == StatementType.STRING:
            self.__push(DataType.STRING, cast(StringLiteral, expr).token)
        elif expr.get_type() == StatementType.NULL:
            self.__push(DataType.NONE, cast(NullLiteral, expr).token)
        else:
            raise NotImplementedError(expr.get_type())

    def __handle_assignment(self, expression: BinaryExpression) -> None:
        if expression.left.get_type() == StatementType.IDENTIFIER:
            self.__handle_expression(expression.right)
            slot_id = self.stack_trace.get_variable(cast(Identifier, expression.left).token)
            self.instructions.push_inst(OpCodeType.STORE, slot_id)
        elif expression.left.get_type() == StatementType.INDEX_EXPRESSION:
            index_expr = cast(IndexExpression, expression.left)
            self.__handle_expression(index_expr.expression)
            self.__handle_expression(expression.right)
            self.__handle_expression(index_expr.index)
            self.instructions.push_inst(OpCodeType.SET_INDEX)
        else:
            raise NotImplementedError(expression.left.get_type())

    def __handle_call_statement(self, call_expr: CallExpression) -> None:
        self.__handle_expression(call_expr.callee)
        for argument in call_expr.arguments:
            self.__handle_expression(argument)
        self.instructions.push_inst(OpCodeType.CALL, len(call_expr.arguments))

    def __handle_index_statement(self, index_expr: IndexExpression) -> None:
        self.__handle_expression(index_expr.expression)
        self.__handle_expression(index_expr.index)
        self.instructions.push_inst(OpCodeType.GET_INDEX)

    def __handle_sequence(self, sequence_expression: SequenceExpression) -> None:
        for elements in sequence_expression.expressions:
            self.__handle_expression(elements)
        self.instructions.push_inst(OpCodeType.MAKE_LIST, len(sequence_expression.expressions))

    def __handle_identifier(self, identifier: Identifier) -> None:
        if self.__is_function(identifier.token):
            self.__push(DataType.FUNCTION, identifier.token)
        else:
            slot_id = self.stack_trace.get_variable(identifier.token)
            self.instructions.push_inst(OpCodeType.LOAD, slot_id)

    def __push(self, data_type: DataType, value: Word) -> None:
        index = self.__add_constant(data_type, value)
        self.instructions.push_inst(OpCodeType.PUSH, index)

    def __is_function(self, token: Word) -> bool:
        raw_token = token.get_raw()
        return raw_token in self.program.frame_names or raw_token in BUILT_IN_METHODS

    def __add_constant(self, data_type: DataType, value: Word | None) -> int:
        raw_data = None if value is None else value.get_raw()
        lookup_key = f"{data_type.value}:{raw_data}"
        if lookup_key in self.raw_symbols:
            return self.raw_symbols[lookup_key]
        match data_type:
            case DataType.INTEGER:
                 self.symbol_table += struct.pack("<BIi", data_type.value, 4, int(raw_data))
            case DataType.BOOLEAN:
                self.symbol_table += struct.pack("<BB", DataType.BOOLEAN.value, value.get_type() == TokenType.K_TRUE)
            case DataType.STRING | DataType.VARIABLE | DataType.FUNCTION:
                raw_data = raw_data[1:-1] if data_type == DataType.STRING else raw_data
                length = len(raw_data)
                self.symbol_table += struct.pack(f"<BI{length}s", data_type.value, length, raw_data.encode('utf-8'))
            case DataType.NONE:
                self.symbol_table += struct.pack("<B", data_type.value)
            case _:
                raise NotImplementedError(data_type)
        self.raw_symbols[lookup_key] = len(self.raw_symbols)
        return self.raw_symbols[lookup_key]

class Instruction:
    def __init__(self):
        self.instructions = list[tuple[OpCodeType, int]]()

    def get_raw(self) -> bytearray:
        raw_instructions = bytearray()
        for instruction in self.instructions:
            raw_instructions += struct.pack("<BH", instruction[0].value, instruction[1])
        return raw_instructions

    def get_count(self) -> int:
        return len(self.instructions)

    def push_inst(self, opcode: OpCodeType, value: int=0) -> int:
        self.instructions.append((opcode, value))
        return self.get_count()

    def update_inst(self, index: int, value: int=0) -> None:
        if index < 0 or index > len(self.instructions) - 1:
            raise LanmoSyntaxError(None, "Compiler faulted (error point: update_inst)")
        og_inst = self.instructions[index]
        self.instructions[index] = (og_inst[0], value)

class StackTrace:
    def __init__(self) -> None:
        self.stack: list[Trace] = list()
        self.available_slots = list()
        self.slot_size = 0

    def push(self, context: StatementType, line: int) -> None:
        self.stack.append(Trace(context, line))

    def pop(self) -> None:
        self.available_slots += list(self.stack[-1].variables.values())
        self.stack.pop()

    def create_variable(self, token: Word) -> int:
        if token.get_raw() in self.stack[-1].variables:
            raise LanmoSyntaxError(token, f"Variable '{token.get_raw()}' is already declared in the scope")
        if len(self.available_slots) != 0:
            slot_id = self.available_slots.pop()
        else:
            slot_id = self.slot_size
            self.slot_size += 1
        self.stack[-1].variables[token.get_raw()] = slot_id
        return slot_id

    def get_variable(self, token: Word) -> int:
        name = token.get_raw()
        for stack_index in range(1, len(self.stack) + 1):
            stack_variables = self.stack[-stack_index].variables
            if name in stack_variables:
                return stack_variables[name]
        raise LanmoSyntaxError(token, f"Variable '{token.get_raw()}' referred before declaration")
