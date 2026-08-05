import sys

from utils.compiler import Compiler
from utils.constants import FILE_EXTENSION, MINOR_VERSION, MAJOR_VERSION, COMPILE_EXTENSION
from utils.exceptions import LanmoSyntaxError


def print_help() -> None:
    print("USAGE:")
    print("    lmc [PROGRAM_PATH] [OPTIONS]")
    print(f"PROGRAM_PATH:    <lm_file>{FILE_EXTENSION}")
    print("OPTIONS:")
    print("    --version    version of the lmc")
    print("    --help       prints this usage")

def print_failure(exception: LanmoSyntaxError, compiler: Compiler) -> None:
    if exception.token is None or compiler.source_path is None:
        path = "" if compiler.source_path is None else f" at {compiler.source_path}"
        print(f"Error{path}:", exception)
        return
    with open(compiler.source_path, 'r') as file:
        source = file.read()
        line_start = source.rfind("\n", 0, exception.token.get_span()[0]) + 1
        column = exception.token.get_span()[0] - line_start
        line = exception.token.get_line() - 1
        lines = source.splitlines()
        print(f"Syntax Error:\nIn file '{compiler.source_path}' at line {line}: ")
        if line - 1 >= 0:
            print(lines[line - 1])
        print(lines[line])
        print(" " * column + "^" * len(exception.token.get_raw()))
        print(exception)


def open_program_file(file_path: str) -> str:
    try:
        with open(file_path) as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: {file_path} file not found")
        sys.exit(1)

def main(args: list[str]) -> None:
    program_file = None
    program_path = None
    if "--version" in args:
        print(f"LANMO Compiler v{MAJOR_VERSION}.{MINOR_VERSION}; Written in python")
        sys.exit(0)
    elif "--help" in args:
        print_help()
        sys.exit(0)
    else:
        for item in args:
            if item.endswith(FILE_EXTENSION):
                program_file = open_program_file(item)
                program_path = item
                break
    if program_file is None:
        print("ERROR: No *.lm file provided")
        print_help()
        sys.exit(1)
    compiler = Compiler(program_path, program_file)
    try:
        byte_code = compiler.compile()
        with open(program_path[:-len(FILE_EXTENSION)] + COMPILE_EXTENSION, 'wb') as file:
            file.write(byte_code)
    except LanmoSyntaxError as l:
        print_failure(l, compiler)
        sys.exit(1)
    except Exception as e:
        print("Error: compiler core broke")
        exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])