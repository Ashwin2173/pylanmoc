import struct
from typing import cast

from utils.constants import BIN_OP_LOOKUP, MAGIC, MAJOR_VERSION, MINOR_VERSION
from utils.exceptions import LanmoSyntaxError
from utils.models import (
    Word,
    Program,
    BlockStatement,
    FunctionStatement, ReturnStatement, ByteBlob, BinaryExpression, ExpressionStatement, IntegerLiteral, StringLiteral,
    BooleanLiteral, Identifier, CallExpression, NullLiteral, IfStatement
)
from utils.enums import StatementType, DataType, OpCodeType, TokenType


class ByteGenerator:
    def __init__(self, program: Program) -> None:
        self.program = program

        self.raw_symbols = dict()
        self.symbol_table = bytearray()
        self.program_code = bytearray()
        self.function_count = 0

        self.__handle_global_statements()

    def pack_byte_code(self) -> bytearray:
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
        index = self.__add_constant(DataType.FUNCTION, function.name)
        bb = self.__handle_block(function.body)
        frame = bytearray()
        frame += struct.pack("<H", index)
        frame += struct.pack("<I", 0)
        frame += struct.pack("<H", 255)
        frame += struct.pack("<I", bb.opcode_count)
        frame += bb.opcode_array
        self.program_code += frame

    def __handle_block(self, block: BlockStatement) -> ByteBlob:
        bb = ByteBlob()
        for statement in block.body:
            if statement.get_type() == StatementType.RETURN_STATEMENT:
                bb.add(self.__handle_return(cast(ReturnStatement, statement)))
            else:
                bb.add(self.__handle_expression(cast(ExpressionStatement, statement)))
        return bb

    def __handle_call_statement(self, call_exp: CallExpression) -> ByteBlob:
        bb = self.__push(DataType.FUNCTION, call_exp.callee)
        for argument in call_exp.arguments:
            bb.add(self.__handle_expression(argument))
        bb.add_raw(struct.pack("<BH", OpCodeType.CALL.value, len(call_exp.arguments)))
        return bb

    def __handle_return(self, return_stmt: ReturnStatement) -> ByteBlob:
        bb = self.__handle_expression(return_stmt.expression)
        bb.add_raw(struct.pack("<BH", OpCodeType.RETURN.value, 0))
        return bb

    def __handle_expression(self, exp: ExpressionStatement) -> ByteBlob:
        if exp.get_type() in BIN_OP_LOOKUP:
            bin_exp: BinaryExpression = cast(BinaryExpression, exp)
            bb = self.__handle_expression(bin_exp.left)
            bb.add(self.__handle_expression(bin_exp.right))
            bb.add_raw(struct.pack("<BH", OpCodeType.BIN_OP.value, BIN_OP_LOOKUP[exp.s_type]))
            return bb
        elif exp.get_type() == StatementType.CALL_EXPRESSION:
            return self.__handle_call_statement(cast(CallExpression, exp))
        elif exp.get_type() == StatementType.IDENTIFIER:
            return self.__push(DataType.VARIABLE, cast(Identifier, exp).token)
        elif exp.get_type() == StatementType.BOOLEAN:
            return self.__push(DataType.BOOLEAN, cast(BooleanLiteral, exp).token)
        elif exp.get_type() == StatementType.INTEGER:
            return self.__push(DataType.INTEGER, cast(IntegerLiteral, exp).token)
        elif exp.get_type() == StatementType.STRING:
            return self.__push(DataType.STRING, cast(StringLiteral, exp).token)
        elif exp.get_type() == StatementType.NULL:
            return self.__push(DataType.NONE, cast(NullLiteral, exp).token)
        raise NotImplementedError(exp.get_type())

    def __push(self, data_type: DataType, value: Word) -> ByteBlob:
        index = self.__add_constant(data_type, value)
        return ByteBlob(
            opcode_array = struct.pack("<BH",OpCodeType.PUSH.value, index),
            opcode_count = 1
        )

    def __add_constant(self, data_type: DataType, value: Word | None) -> int:
        raw_data = None if value is None else value.get_raw()
        lookup_key = f"{data_type.value}{raw_data}"
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
