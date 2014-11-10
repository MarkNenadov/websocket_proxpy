import sys
def fatal_fail(message):
    if message is not None:
        print(message)
    sys.exit(1)