import sys

from utils.compiler import Compiler
from utils.constants import FILE_EXTENSION, MINOR_VERSION, MAJOR_VERSION, COMPILE_EXTENSION


def print_help() -> None:
    print("USAGE:")
    print("    lmc [PROGRAM_PATH] [OPTIONS]")
    print(f"PROGRAM_PATH:    <lm_file>{FILE_EXTENSION}")
    print("OPTIONS:")
    print("    --version    version of the lmc")
    print("    --help       prints this usage")

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
    compiler = Compiler(program_file)
    byte_code = compiler.compile()
    with open(program_path[:-len(FILE_EXTENSION)] + COMPILE_EXTENSION, 'wb') as file:
        file.write(byte_code)

if __name__ == "__main__":
    main(sys.argv[1:])