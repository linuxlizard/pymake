import pytest

import run

# Test all the complex ways GNU Make handles recipe prefix (default <tab>).
#
# GNU Make will test a <tab> character first, then seek directives, and if
# a directive not found, then attempt to treat the line as a Recipe. If there's
# no active Rule, then GNU Make flags an error.
# See function eval() in src/read.c  GNU Make 4.3

def _verify(err, expect):
    # expect can be a string or a list (oops had to update code to handle
    # different error strings for shell output)
    if isinstance(expect,str):
        assert expect in err
    else:
        assert any((s in err for s in expect))
    
def run_fail_test(makefile, expect):
    err = run.gnumake_should_fail(makefile)
    print("err=",err)
    _verify(err, expect)
    
    err = run.pymake_should_fail(makefile)
    print("err=",err)
    _verify(err, expect)

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
    run_fail_test(makefile, "missing 'endef', unterminated 'define'")

def test_var_assign_before_first_rule():
    # variable assignment allowed as long as before the first rule
    makefile = """
	a := 42
foo:
	@echo $(a)
"""
    run_test(makefile, "42")

def test_leading_tab_before_rule():
    makefile = """
	$(info leading tab before any rules)
@:;@:
"""
    run_fail_test(makefile, "recipe commences before first target")

def test_tab_comment():
    makefile = """
	# this is a comment with leading tab and is ignored
foo:
	@echo foo
"""
    run_test(makefile, "foo")    

def test_tab_tab_comment():
    makefile = """
		# this is a comment with leading tab tab and is ignored
foo:
	@echo foo
"""
    run_test(makefile, "foo")    

def test_tab_spaces_comment():
    makefile = """
	     # this is a comment with leading tab and some spaces and is ignored
foo:
	@echo foo
"""
    run_test(makefile, "foo")    

def test_bare_tab():
    # line with just a bare tab is ignored
    makefile = """
	
foo:
	@echo foo
"""
    run_test(makefile, "foo")    

def test_recipe_missing_tab():
    makefile = """
# no tab character on the recipe!
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

def test_recipe_with_ifdef_spaces():
    # should work fine
    makefile = """
FOO:=1
foo:
    ifdef FOO
	@echo foo
    endif
"""
    run_test(makefile, "foo")

def test_recipe_with_ifdef_tabs():
    # the ifdef has a leading tab and we're in a Rule therefore the ifdef is
    # treated as a Recipe.
    #
    # will fail with 'ifdef: No such file or directory'
    makefile = """
FOO:=1

foo:
	ifdef FOO
	@echo foo
	endif
"""
    run_fail_test(makefile, ('No such file or directory', 'not found'))

def test_tab_before_recipe():
    makefile="""
FOO:=1

# because we haven't seen a Recipe yet, this is treated as just a regular line.
	ifdef FOO
    $(info FOO=$(FOO))
endif

# "rule without a target" for
# "compatibility with SunOS 4 make"
: foo
	@echo error\\\\! should not see this
	exit 1

foo:
ifdef FOO
	@echo foo
endif
"""
    run_test(makefile, "FOO=1\nfoo")

