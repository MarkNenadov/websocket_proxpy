import sys


def fatal_fail(message: str or None) -> None:
    if message:
        print(message)
    sys.exit(1)
