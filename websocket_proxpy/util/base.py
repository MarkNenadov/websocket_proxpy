import sys


def fatal_fail(message):
    if message:
        print(message)
    sys.exit(1)
