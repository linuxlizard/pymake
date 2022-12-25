import run

# check for errors in variable names
# TODO finish this test

def test1():
    makefile="""
FOO BAR:=42
@:;@:
"""
    # error empty variable name
#    run.pymake_should_fail(makefile)
    run.gnumake_should_fail(makefile)

