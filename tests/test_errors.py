import run

# For the most part, I've started this file with the individual "errorNN.mk" I
# collected when I was first working on pymake.  Some of these will have
# similar tests in more specialized test files.
# 20221224

def run_test(makefile, expect):
    err = run.gnumake_should_fail(makefile)
    print("err=",err)
    assert expect in err, err

def test_error_function():
    makefile="""
# this is a test of the error function

$(error hello, world)
@:;@:
"""
    run_test(makefile, "*** hello, world")

def test_error_recipe_commences_before_first_target_directive():
# The leading tabs mean this is treated as a recipe.
# "recipe commences before first target"
#
    makefile="""
	ifdef CC
		$(info CC=$(CC))
	else
		$(error CC is not set)
	endif

@:;@:
"""
    run_test(makefile,"*** recipe commences before first target")

def test_error_case_sensitive_directive():
# directives are case sensitive; 
# *** missing separator. Stop.
    makefile="""
IFDEF CC
    $(info CC=$(CC))
ENDIF

@:;@:
"""
    run_test(makefile, "*** missing separator")

def test_error_conditional_directive_syntax():
    # parsed as a conditional directive but looks like a rule
    makefile="""
# *** invalid syntax in conditional.
ifdef : ; @echo I am here $@

# Note if split across multiple lines, is still a conditional.
# Treated as conditional directives but looks like a rule.
ifdef : 
	@echo I am here $@
endif

@:;@:
"""
    run_test(makefile,"*** invalid syntax in conditional")

def test_error_empty_variable_name():
    # parsed as an assignment statement
    makefile = """
# "empty variable name"
:=foo

@:;@:
"""
    run_test(makefile,"*** empty variable name")

def test_error_ifeq_paren():
    # "Invalid syntax in conditional."
    makefile = """
# try to match "(" == "(" which
ifeq ((,()
endif

@:;@:
"""
    run_test(makefile,"*** invalid syntax in conditional")

def test_error_recipe_commences_before_first_target():
    # test cases of TAB (or other rule char) being used in strange places.
    # not treated as a rule (ignored)
    makefile="""
	# foo bar baz

# valid
	FOO:=BAR

# treated as a rule
# "recipe commences before first target"
	$(info FOO=$(FOO))

@:;@:
"""
    run_test(makefile,"*** recipe commences before first target")

def test_error_split_cond():
# splitting a single line with a conditional (inserting a conditional directive
# inside a function call doesn't seem to be valid, luckily)
    makefile = """
# *** unterminated call to function 'info': missing ')'.
$(info hello world \
ifdef FOO
	I am foo\
else
	I am not foo\
endif
)

@:;@:
"""
    run_test(makefile,"*** unterminated call to function 'info': missing ')'")

def test_error_tab_unterminated_define():
# Leading <tab> creates confusion.  
# "missing 'enddef', unterminated 'define'"
# Might be a GNU Make bug?  Works fine with <space>endef as opposed to this <tab>endef
    makefile="""
	define foo
		echo foo
	endef

define bar
endef

@:;@:
"""
    run_test(makefile,"*** missing 'endef', unterminated 'define'")

def test_error_space_after_backslash():
    # "missing separator"
    # The space after backslash is error.
    # This test is a little difficult becuase python is interpretting the \ in the string
    makefile="""# the following throws error "missing separator"
# The \\ isn't treated as a line continuation. The "newline!" is trying to be
# parsed as a statement (assignment|rule|directive)
backslash-space-eol : 
	@echo $@ \\ 
newline!
# there is space after the backslash in the above rule
"""
    run_test(makefile, "*** missing separator")

def test_error_comments_in_weird_spaces():
# the following throws error "missing separator"
    makefile="""    
comments-in-weird-spaces\
# hello world
=\
# hello world
42
"""
    run_test(makefile, "*** missing separator")

def test_many_trailing_spaces():
    # trailing spaces throw off backslashes
    # The black line with \\ has a trailing space (the line before 'foo')
    makefile="""
# the 
many-empty-lines\\
=\\
    \\  
foo
$(info = foo=$(many-empty-lines))
@:;@:
"""
    run_test(makefile, "*** missing separator")

def test_no_target():
    makefile="""
foo = bar

# this makefile has no targets 
"""
    run_test(makefile, "*** No targets")

def test_target_specific_variable_error():
    makefile="""
# Combine target specific variable with Error. 
# "commands commence before first target"
#
# Note: 
#   bar : BAR=FOO ; @echo bar bar bar  
# works. The ; recipe is ignored
#
bar : BAR=FOO 
	@echo bar bar bar
"""
    run_test(makefile, "*** recipe commences before first target")

def test_foo():
    makefile="""
foo
"""
    run_test(makefile, "*** missing separator")

def test_python():
    makefile="""#!/usr/bin/env python3

# A few times I've accidentally fed my python scripts to my makefile parser
# Yes, it's a silly test but as of this writing my parser will successfully
# accept this file (!).
# davep 08-Oct-2014

import sys

import itertools

import hexdump
from sm import *

eol = set("\r\n")
whitespace = set( ' \t' )

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
"""
    run_test(makefile, "*** missing separator")

def test_define_rulename():
    makefile="""# not valid
define : ; @echo $@
"""
    run_test(makefile, "*** missing 'endef', unterminated 'define'")

def test_comment_cuddled_endif():
    makefile="""
define block = 
the comment cuddled up to the endef breaks the endef
endef#this is a commment
"""
    run_test(makefile, "*** missing 'endef', unterminated 'define'")

def test_multiple_else_conditional():
    makefile="""
# *** only one `else' per conditional.  Stop.
ifdef FOO
else
else
endif

@:;@:
"""
    run_test(makefile, "*** only one 'else' per conditional")

def test_ifdef_whitespace_paren():
    # missing separator
    makefile="""# whitespace required
ifeq($(foo),1)
endif
@:;@:
"""
    run_test(makefile, "*** missing separator")

def test_ifdef_whitespace_quotes():
    # missing separator
    makefile="""# whitespace required
ifeq"$(foo)","1"
endif
@:;@:
"""
    run_test(makefile, "*** missing separator")

def test_ifdef_missing_whitespace():
    # missing separator
    makefile="""
ifdef$(FOO)
endif
@:;@:
"""
    run_test(makefile, "*** missing separator")

def test_only_one_else_per_conditional():
    makefile = """
ifdef FOO
else
else
endif
@:;@:
"""
    run_test(makefile, "*** only one 'else' per conditional")
    
def test_only_one_else_again():
    makefile="""
ifdef FOO
else
else ifdef BAR
endif
@:;@:
"""
    run_test(makefile, "*** only one 'else' per conditional")

def test_missing_endif():
    makefile="""
ifdef A
else
# missing endif
"""
    run_test(makefile,"*** missing 'endif'")

def test_extraneous_endif():
    makefile="""
# extraneous endif
ifdef FOO
else
endif
endif
"""
    run_test(makefile,"*** extraneous 'endif'")

def test_floating_endif():
    # extraneous else
    makefile="""
ifdef FOO
else
endif

else
"""
    run_test(makefile,"*** extraneous 'else'")

def test_unbalanced_parenthesis():
    makefile="""
# this unbalanced parenthesis valid; treated as a string char
foo:=$(subst ee,EE,feet on the street))
paren:=)
ifneq ($(lastword $(foo)),strEEt$(paren))
$(error missing strEEt$(paren) foo=$(lastword $(foo)))
endif

# missing closing )
# error24.mk:6: *** unterminated call to function `subst': missing `)'.  Stop.
path:=$(subst :, ,$(PATH)

@:;@:
"""
    run_test(makefile,"*** unterminated call to function 'subst': missing ')'")

def test_empty_variable_name():
    makefile="""
# error "empty variable name"

# <space>=42
 =42

@:;@:
"""
    run_test(makefile,"*** empty variable name")

def test_unterminated_variable_reference():
    makefile="""
# *** unterminated variable reference.
bar:=$(bar}

@:;@:
"""
    run_test(makefile,"*** unterminated variable reference.")

def test_load_dollar():
    makefile="""
# *** missing separator.
# dollar sign alone on a line, no whitespace
$

@:;@:
"""
    run_test(makefile, "*** missing separator")

