#!/usr/bin/env python3

# Regression tests for pymake.py
#
# Test Makefile recipe tokenizing
#
# davep 24-Sep-2014

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

import hexdump
from sm import *
from run_tests import run_tests_list
import vline

def big_recipes_test() :
    # parse a full block of recipes! 

    recipe_test_list = ( 
# use """ to make easier to read tests
# -------------
#
    ("""\techo foo 1
\techo bar 2
\techo baz 3
\tdate
# this is a comment at column 0

# this is a line after a blank line
# """,

    RecipeList( [Recipe( [Literal("echo foo 1")]),Recipe( [Literal("echo bar 2")]),Recipe( [Literal("echo baz 3")]),Recipe( [Literal("date")])])
    ),

# -------------
("""; echo semicolon-foo
# 
this-is-an-assignment=42""", 
    RecipeList( [Recipe( [Literal("echo semicolon-foo")])])
),
# -------------

        ( "\n\tgcc -c -Wall -o $@ $<",
            RecipeList( [Recipe( [Literal("gcc -c -Wall -o "),
                                  VarRef([Literal("@")]),
                                  Literal(" "),
                                  VarRef( [Literal("<")] ), 
                                  Literal( "" ),
                                 ]
                               )
                        ]
                      )
        ),

# -- from ffmpeg
("""
	$(DATA_FILES) $(EXAMPLES_FILES)
	$(Q)mkdir -p "$(DATADIR)/examples"
	$(INSTALL) -m 644 $(DATA_FILES) "$(DATADIR)"
	$(INSTALL) -m 644 $(EXAMPLES_FILES) "$(DATADIR)/examples"
""", () ),

        ( "\n\tgcc -c -Wall -o $@ $<", () ),

("""
	@echo $@
# the $(info) is error "commands commence before first target"
#$(info inside varref recipes)
	@echo varref recipe
# this $(info) is not executed (not seeing the message)
	@echo varref recipe info=$(info inside varref recipes)
# this $() is executed (seeing the date)
	@echo varref recipe date=$(shell date)
    # this $(error IS hit) (this comment is valid but Vim highlights as error)
	@echo varref recipe info=$(error inside varref recipes)

end-of-varrefs=yeah this ends varrefs rule for sure
""", () ),

("""; @echo lots of spaces in weird places 

# the next line starts with a raw <tab>. Is valid. (starts empty shell? ignored?)
	

# the next line is <space><tab><EOL>. Is valid. (ignored)
 	

# the next line starts with a raw <tab>. Is valid. (Sent to shell)
	foo=bar printenv "foo"

	@echo I am still inside $@

# the next line is <tab><tab>. Is valid. The tabs are eaten.
		@echo tab tab

# the next line is <tab><space><tab>. Is valid. The tabs/spaces are eaten.
	 	@echo tab space tab

# the next line is <tab><space><tab><space><space><space>. Is valid. The tabs/spaces are eaten.
	 	   @echo tab space tab space space space

# the next line is has trailing <tab>s and <space>s; can see the whitespace on a hexdump of this output
# the trailing whitespace is preserved
	@echo I have trailing whitespacespaces                  	   	

# this line ends the recipe; note can be interpretted as either an assignment or a shell recipe
 	foo=bar printenv "foo"

""", () ),

#------
    # from the Linux kernel 3.12.5 clean rule (removed the 'rm' to make safe)
(r"""
	@find $(if $(KBUILD_EXTMOD), $(KBUILD_EXTMOD), .) $(RCS_FIND_IGNORE) \
		\( -name '*.[oas]' -o -name '*.ko' -o -name '.*.cmd' \
		-o -name '*.ko.*' \
		-o -name '.*.d' -o -name '.*.tmp' -o -name '*.mod.c' \
		-o -name '*.symtypes' -o -name 'modules.order' \
		-o -name modules.builtin -o -name '.tmp_*.o.*' \
		-o -name '*.gcno' \) -type f -print | xargs 
                """, () ),
#------
# backslash in string
(r"""
	@printf "foo bar baz\n" \
@printf "FOO BAR BAZ\n" 
""", () ),
#------

        ( ";echo foo", RecipeList( [Recipe( [Literal("echo foo")])]) ),

        ( ";echo foo\n\techo bar", 
            RecipeList( [Recipe( [Literal("echo foo")]),Recipe( [Literal("echo bar")])])
        ),
        
        ( ";echo foo\n\t    echo bar", 
            RecipeList( [Recipe( [Literal("echo foo")]),Recipe( [Literal("echo bar")])])
        ),

        ( ";echo foo\n\techo bar\n\techo baz\n\n\n\n\n", 
            RecipeList( [Recipe( [Literal("echo foo")]),
                         Recipe( [Literal("echo bar")]),
                         Recipe( [Literal("echo baz")])])
        ),

        ( ";echo foo\n\techo bar\n\techo baz\n\nthis is an ugly comment", 
            RecipeList( [Recipe( [Literal("echo foo")]),
                         Recipe( [Literal("echo bar")]),
                         Recipe( [Literal("echo baz")])])
        ),

    )

    # these must fail
    fail_tests = ( 
        ( "foo:\n; @echo bar", () )
    )

#    run_tests_list(recipe_test_list,tokenize_recipe_list)

    # test make_recipe_block() which splits apart the makefile lines into
    # separate recipe lines
    for test in recipe_test_list : 
        s,v = test

        print( "s=[\n{0}  ]\n".format(hexdump.dump(s,16)),end="")
        file_lines = s.split("\n")[:-1]
        lines = [ line+"\n" for line in file_lines ]

        semicolon_recipe = ""
        if s.startswith(";") :
            assert 0

        my_iter = ScannerIterator( lines )
        recipe_list = vline.make_recipe_block(my_iter,semicolon_recipe)
        print("recipe_list={0}".format(recipe_list.makefile()))
        print("v={0}".format(v.makefile()))

        assert v==recipe_list


def single_recipe_test() : 
    # simple single recipes

    test_list = ( 
        (   "	$(CC) -g -wall -o $@ $^", 
            Recipe( [Literal(""),VarRef( [Literal("CC")]),Literal(" -g -wall -o "),VarRef( [Literal("@")]),Literal(" "),VarRef( [Literal("^")]),Literal("")]) 
        ),

        (   "; $(CC) -g -wall -o $@ $^", 
            Recipe( [Literal(""),VarRef( [Literal("CC")]),Literal(" -g -wall -o "),VarRef( [Literal("@")]),Literal(" "),VarRef( [Literal("^")]),Literal("")]) 
        ),

        ( "	@echo this \\\nis\\\na\\\ntest\n", Recipe( [Literal("@echo this \\\nis\\\na\\\ntest" )])),

        # From linux kernel
        (   r"""	$(if $(KBUILD_VERBOSE:1=),@)$(MAKE) -C $(KBUILD_OUTPUT) \
	KBUILD_SRC=$(CURDIR) \
	KBUILD_EXTMOD="$(KBUILD_EXTMOD)" -f $(CURDIR)/Makefile \
	$(filter-out _all sub-make,$(MAKECMDGOALS))
""",
    Recipe( [Literal(""),VarRef( [Literal("if "),VarRef( [Literal("KBUILD_VERBOSE:1=")]),Literal(",@")]),Literal(""),VarRef( [Literal("MAKE")]),Literal(" -C "),VarRef( [Literal("KBUILD_OUTPUT")]),Literal(" \\\n\tKBUILD_SRC="),VarRef( [Literal("CURDIR")]),Literal(" \\\n\tKBUILD_EXTMOD=\""),VarRef( [Literal("KBUILD_EXTMOD")]),Literal("\" -f "),VarRef( [Literal("CURDIR")]),Literal("/Makefile \\\n\t"),VarRef( [Literal("filter-out _all sub-make,"),VarRef( [Literal("MAKECMDGOALS")]),Literal("")]),Literal("")])
        ),

    # end of tests
    )

    run_tests_list( test_list,tokenize_recipe )

def run() : 
    single_recipe_test()
    big_recipes_test()

if __name__=='__main__':
    run()

