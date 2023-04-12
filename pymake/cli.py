import sys

def run():
    prompt = "(mdb) "

    while True:
        sys.stdout.write(prompt)
        sys.stdout.flush()

        command = sys.stdin.readline().strip()

        if command in ('q', "quit"):
            # FIXME should exit the entire pymake debugger process
            break

        if command in ('c', "continue"):
            break

