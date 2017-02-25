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
from pymake import *
from run_tests import run_tests_list
import vline

def big_recipes_test() :
	# parse a full block of recipes! 

	recipe_test_list = ( 
# use """ to make easier to read tests
# -------------
#
#	("""\techo foo 1
#\techo bar 2
#\techo baz 3
#\tdate
## this is a comment at column 0
#
## this is a line after a blank line
## """,
#
#	RecipeList( [Recipe( [Literal("echo foo 1")]),Recipe( [Literal("echo bar 2")]),Recipe( [Literal("echo baz 3")]),Recipe( [Literal("date")])])
#	),

# -------------

		( "\tgcc -c -Wall -o $@ $<",
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
("""	 $(DATA_FILES) $(EXAMPLES_FILES)
	$(Q)mkdir -p "$(DATADIR)/examples"
	$(INSTALL) -m 644 $(DATA_FILES) "$(DATADIR)"
	$(INSTALL) -m 644 $(EXAMPLES_FILES) "$(DATADIR)/examples"
""", 
			RecipeList( [Recipe( [Literal(""),VarRef( [Literal("DATA_FILES")]),Literal(" "),VarRef( [Literal("EXAMPLES_FILES")]),Literal("")]),Recipe( [Literal(""),VarRef( [Literal("Q")]),Literal("mkdir -p \""),VarRef( [Literal("DATADIR")]),Literal("/examples\"")]),Recipe( [Literal(""),VarRef( [Literal("INSTALL")]),Literal(" -m 644 "),VarRef( [Literal("DATA_FILES")]),Literal(" \""),VarRef( [Literal("DATADIR")]),Literal("\"")]),Recipe( [Literal(""),VarRef( [Literal("INSTALL")]),Literal(" -m 644 "),VarRef( [Literal("EXAMPLES_FILES")]),Literal(" \""),VarRef( [Literal("DATADIR")]),Literal("/examples\"")])]) 
		),

		#\tgcc\
		#-c\
		# -Wall\
		# -o\
		# $@\
		# $<
		( "\tgcc\\\n -c\\\n -Wall\\\n -o\\\n $@\\\n $<", 
			RecipeList([Recipe([Literal("gcc\\\n -c\\\n -Wall\\\n -o\\\n "),VarRef([Literal("@")]),Literal("\\\n "),VarRef([Literal("<")]),Literal("")])])
		),

		("""	@echo $@
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
""", 
		RecipeList( [Recipe( [Literal("@echo "),VarRef( [Literal("@")]),Literal("")]),Recipe( [Literal("@echo varref recipe")]),Recipe( [Literal("@echo varref recipe info="),VarRef( [Literal("info inside varref recipes")]),Literal("")]),Recipe( [Literal("@echo varref recipe date="),VarRef( [Literal("shell date")]),Literal("")]),Recipe( [Literal("@echo varref recipe info="),VarRef( [Literal("error inside varref recipes")]),Literal("")])])

		),

		("; @echo lots of spaces in weird places ", 
"""# the next line starts with a raw <tab>. Is valid. (starts empty shell? ignored?)
	

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

""", 
		RecipeList( [Recipe( [Literal("@echo lots of spaces in weird places ")]),Recipe( [Literal("")]),Recipe( [Literal("foo=bar printenv \"foo\"")]),Recipe( [Literal("@echo I am still inside "),VarRef( [Literal("@")]),Literal("")]),Recipe( [Literal("@echo tab tab")]),Recipe( [Literal("@echo tab space tab")]),Recipe( [Literal("@echo tab space tab space space space")]),Recipe( [Literal("@echo I have trailing whitespacespaces				  \t   \t")])])
		),

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
				""", 
		RecipeList( [Recipe( [Literal("@find "),VarRef( [Literal("if "),VarRef( [Literal("KBUILD_EXTMOD")]),Literal(", "),VarRef( [Literal("KBUILD_EXTMOD")]),Literal(", .")]),Literal(" "),VarRef( [Literal("RCS_FIND_IGNORE")]),Literal(" \\\n\t\t\\( -name '*.[oas]' -o -name '*.ko' -o -name '.*.cmd' \\\n\t\t-o -name '*.ko.*' \\\n\t\t-o -name '.*.d' -o -name '.*.tmp' -o -name '*.mod.c' \\\n\t\t-o -name '*.symtypes' -o -name 'modules.order' \\\n\t\t-o -name modules.builtin -o -name '.tmp_*.o.*' \\\n")])])
				),
#------
# backslash in string
(r"""
	@printf "foo bar baz\n" \
@printf "FOO BAR BAZ\n" 
""", RecipeList( [Recipe( [Literal("@printf \"foo bar baz\\n\" \\\n")])]) ),
#------

		# The following tests validate capturing a recipe after a ";" after the
		# prerequisites. The tokenizer expects the first character to be a ";"
		# in this case.  (The prerequisite tokenizer will leave the string
		# iterator in that state.)
		( ";echo foo\n","", RecipeList( [Recipe( [Literal("echo foo")])]) ),

		( ";echo foo\n","\techo bar\n", 
			RecipeList( [Recipe( [Literal("echo foo")]),Recipe( [Literal("echo bar")])])
		),
		
		# whitespace before recipe should be eaten
		( ";	echo foo\n","\t	echo bar\n", 
			RecipeList( [Recipe( [Literal("echo foo")]),Recipe( [Literal("echo bar")])])
		),

		( ";echo foo\n","\techo bar\n\techo baz\n\n\n\n\n", 
			RecipeList( [Recipe( [Literal("echo foo")]),
						 Recipe( [Literal("echo bar")]),
						 Recipe( [Literal("echo baz")])])
		),

		( ";echo foo\n", "\techo bar\n\techo baz\n\nthis is an ugly comment", 
			RecipeList( [Recipe( [Literal("echo foo")]),
						 Recipe( [Literal("echo bar")]),
						 Recipe( [Literal("echo baz")])])
		),


		("; echo semicolon-foo\n", "# \n this-is-an-assignment=42\n", 
			RecipeList( [Recipe( [Literal("echo semicolon-foo")])])
		),


	# end of recipe_test_list
	)

	# these must fail
	fail_tests = ( 
		( "foo:\n; @echo bar", () )

		# NEED MOAR TESTS!
	)

	# test make_recipe_block() which splits apart the makefile lines into
	# separate recipe lines
	for idx,test in enumerate(recipe_test_list) : 
		# tests can be three fields instead of the regular two:
		#   the (optional) recipe after the prerequesites (follows the ";")
		#   the recipe(s) string
		#   the RecipeList() validation 
		if len(test)==3:
			semicolon_string,test_string,validation = test
		else : 
			test_string,validation = test
			semicolon_string = ""

		print( "s=[\n{0}  ]\n".format(hexdump.dump(test_string,16)),end="")
		# The tokenizer expects to find an array of strings, not one solid string.
		# Break into an array of strings but restore the eof to keep the
		# tokenizer state machines happy.
		file_lines = test_string.split("\n")
		lines = [ line+"\n" for line in file_lines ]

		print('lines=',lines)

		recipe_list = parse_recipes(ScannerIterator(lines),semicolon_string)
		print("recipe_list={0}".format(str(recipe_list)))
		print("recipe_list=[\n{0}\n]".format(recipe_list.makefile()))
		print("v={0}".format(validation.makefile()))

		assert validation==recipe_list,(idx,)


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
#	single_recipe_test()
	big_recipes_test()

if __name__=='__main__':
	run()

