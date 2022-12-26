import run

def run_test(makefile, expect):
    out = run.gnumake_string(makefile)
    print("out=",out)
    assert expect in out, out

def test_warning_function():
    makefile="""
$(warning this is your only warning)
@:;@:
"""
    run_test(makefile, "this is your only warning")

def test_warning_ifeq_extraneous_text():
    # extraneous text after 'ifeq' directive
    makefile="""
ifeq (a,a)q
endif

# same
#ifeq (a,a),
#ifeq (a,a))

@:;@:
"""
    run_test(makefile, "extraneous text after 'ifeq' directive")

def test_extraneous_text_after_else():
    makefile="""
ifdef FOO
else this should throw "Extraneous text after else directive"
endif

@:;@:
"""
    run_test(makefile, "extraneous text after 'else' directive")

def test_else_ifeq_whitespace():
    # extraneous text after 'else' directive
    # (the ifeq isn't correctly parsed because of missing whitespace)
    makefile="""   
# whitespace required. Sort of.  "extraneous text after 'else' directive"
ifeq ($(foo),1)
else ifeq($(foo),2)
endif
@:;@:
"""
    run_test(makefile, "extraneous text after 'else' directive")

