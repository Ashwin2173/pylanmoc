import struct
from typing import cast

from utils.constants import BIN_OP_LOOKUP, MAGIC, MAJOR_VERSION, MINOR_VERSION, BUILT_IN_METHODS
from utils.exceptions import LanmoSyntaxError
from utils.models import (
    Word,
    Program,
    Identifier,
    NullLiteral,
    StringLiteral,
    BooleanLiteral,
    IntegerLiteral,
    CallExpression,
    BlockStatement,
    ReturnStatement,
    BinaryExpression,
    FunctionStatement,
    ExpressionStatement,
)
from utils.enums import StatementType, DataType, OpCodeType, TokenType

class ByteCodeGenerator:
    def __init__(self, program: Program) -> None:
        self.program = program

        self.raw_symbols = dict()
        self.symbol_table = bytearray()
        self.program_code = bytearray()
        self.inst_pointer: Instruction | None = None
        self.function_count = 0

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
        self.inst_pointer = Instruction()
        index = self.__add_constant(DataType.FUNCTION, function.name)
        self.__handle_block(function.body)
        frame = bytearray()
        frame += struct.pack("<H", index)
        frame += struct.pack("<I", 0)
        frame += struct.pack("<H", 255)
        frame += struct.pack("<I", self.inst_pointer.get_count())
        frame += self.inst_pointer.get_raw()
        self.program_code += frame

    def __handle_block(self, block: BlockStatement) -> None:
        for statement in block.body:
            if statement.get_type() == StatementType.RETURN_STATEMENT:
                self.__handle_return(cast(ReturnStatement, statement))
            else:
                self.__handle_expression(cast(ExpressionStatement, statement))

    def __handle_call_statement(self, call_exp: CallExpression) -> None:
        self.__handle_expression(call_exp.callee)
        for argument in call_exp.arguments:
            self.__handle_expression(argument)
        self.inst_pointer.push_inst(OpCodeType.CALL, len(call_exp.arguments))

    def __handle_return(self, return_stmt: ReturnStatement) -> None:
        self.__handle_expression(return_stmt.expression)
        self.inst_pointer.push_inst(OpCodeType.RETURN, 0)

    def __handle_expression(self, exp: ExpressionStatement) -> None:
        if exp.get_type() in BIN_OP_LOOKUP:
            bin_exp: BinaryExpression = cast(BinaryExpression, exp)
            self.__handle_expression(bin_exp.left)
            self.__handle_expression(bin_exp.right)
            self.inst_pointer.push_inst(OpCodeType.BIN_OP.value, BIN_OP_LOOKUP[exp.s_type])
        elif exp.get_type() == StatementType.CALL_EXPRESSION:
            self.__handle_call_statement(cast(CallExpression, exp))
        elif exp.get_type() == StatementType.IDENTIFIER:
            self.__handle_identifier(cast(Identifier, exp))
        elif exp.get_type() == StatementType.BOOLEAN:
            self.__push(DataType.BOOLEAN, cast(BooleanLiteral, exp).token)
        elif exp.get_type() == StatementType.INTEGER:
            self.__push(DataType.INTEGER, cast(IntegerLiteral, exp).token)
        elif exp.get_type() == StatementType.STRING:
            self.__push(DataType.STRING, cast(StringLiteral, exp).token)
        elif exp.get_type() == StatementType.NULL:
            self.__push(DataType.NONE, cast(NullLiteral, exp).token)
        else:
            raise NotImplementedError(exp.get_type())

    def __handle_identifier(self, identifier: Identifier) -> None:
        raw_token = identifier.token.get_raw()
        if raw_token in self.program.frame_names or raw_token in BUILT_IN_METHODS:
            self.__push(DataType.FUNCTION, identifier.token)
        else:
            self.__push(DataType.VARIABLE, identifier.token)

    def __push(self, data_type: DataType, value: Word) -> None:
        index = self.__add_constant(data_type, value)
        self.inst_pointer.push_inst(OpCodeType.PUSH, index)

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