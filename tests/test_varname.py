import run

# check for errors in variable names
# TODO finish this test

def test1():
    makefile="""
FOO BAR:=42
@:;@:
"""

    # error empty variable name
    should_fail(makefile)

