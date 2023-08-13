import sys


def fatal_fail(message: str) -> None:
    if message:
        print(message)
    sys.exit(1)
