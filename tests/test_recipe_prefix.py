import pytest

import run

# Test all the complex ways GNU Make handles recipe prefix (default <tab>).
#
# GNU Make will test a <tab> character first, then seek directives, and if
# a directive not found, then attempt to treat the line as a Recipe. If there's
# no active Rule, then GNU Make flags an error.
# See function eval() in src/read.c  GNU Make 4.3

def run_fail_test(makefile, expect):
    err = run.gnumake_should_fail(makefile)
    print("err=",err)
    assert expect in err

    err = run.pymake_should_fail(makefile)
    print("err=",err)
    assert expect in err

def run_test(makefile, expect):
    out = run.gnumake_string(makefile)
    print("out=",out)
    assert expect in out, out

    out = run.pymake_string(makefile)
    print("out=",out)
    assert expect in out

def test1():
    # normal everyday rule+recipe
    makefile="""
foo:
	@echo foo
"""
    run_test(makefile, "foo")

@pytest.mark.skip(reason="define not yet implemented in pymake")
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

@pytest.mark.skip(reason="define not yet implemented in pymake")
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
    run_fail_test(makefile, "missing 'endef', unterminated 'define'")

@pytest.mark.skip(reason="recipeprefix TODO")
def test_var_assign_before_first_rule():
    # variable assignment allowed as long as before the first rule
    makefile = """
	a := 42
foo:
	@echo $(a)
"""
    run_test(makefile, "42")

@pytest.mark.skip(reason="recipeprefix TODO")
def test_leading_tab_before_rule():
    makefile = """
	$(info leading tab before any rules)
@:;@:
"""
    run_fail_test(makefile, "recipe commences before first target")

@pytest.mark.skip(reason="recipeprefix TODO")
def test_tab_comment():
    makefile = """
	# this is a comment with leading tab and is ignored
foo:
	@echo foo
"""
    run_test(makefile, "foo")    

def test_recipe_missing_tab():
    makefile = """
#	# this is a comment with leading tab and is ignored
foo:
    @echo foo
"""
    run_fail_test(makefile, "missing separator")

def test_tab_ifdef():
    makefile = """
FOO=1
	ifdef FOO
$(info FOO=$(FOO))
	endif
@:;@:
"""
    run_test(makefile, "FOO=1")    
