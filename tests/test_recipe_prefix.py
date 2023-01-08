import run

# test all the complex ways GNU Make handles recipe prefix (default <tab>)

def run_fail_test(makefile, expect):
    err = run.gnumake_should_fail(makefile)
    print("err=",err)

def run_test(makefile, expect):
    out = run.gnumake_string(makefile)
    print("out=",out)
    assert expect in out, out

def test1():
    makefile="""
foo:
	@echo foo
"""
    run_test(makefile, "foo")

def test_define():
    # define can have a leading tab
    # but endef cannot
    makefile="""
	define DAVE
	42
endef
foo:
	@echo $(DAVE)
"""
    run_test(makefile, "42")

def test_error_define_endef():
    # define can have a leading tab
    # but endef cannot
    makefile="""
	define DAVE
	42
	endef
foo:
	@echo $(DAVE)
"""
    run_fail_test(makefile, "*** missing 'endef', unterminated 'define'")

def test_var_assign_before_first_rule():
    # variable assignment allowed as long as before the first rule
    makefile = """
	a := 42
foo:
	@echo $(a)
"""
    run_test(makefile, "42")

