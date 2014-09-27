#!/usr/bin/env python3

# test tokenizing variable reference
#
# moved to own file 
# davep 27-sep-2014

import sys

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

from sm import *

def run():

    variable_ref_tests = ( 
        # string    result
        ("$(CC)",   ("$(","CC",")")),
        ("$a",   ("$","a",)),
        ("$($$)",      ("$(","$$",")",)),
        ("$($$$$$$)",      ("$(","$$$$$$",")",)),
        ("$( )",   ("$("," ",")")),
        ("$(    )",   ("$(","    ",")")),
        ("$( CC )", ("$("," CC ", ")")),
        ("$(CC$$)",   ("$(","CC$$", ")")),
        ("$($$CC$$)",   ("$(","$$CC$$", ")")),
        ("$($(CC)$$)",   ("$(","$(","CC", "$$",")",")")),
        ("$($$$(CC)$$)",   ("$(","$$","$(","CC",")","$$", ")")),
        ("$(CC$(LD))",   ("$(","CC","$(","LD",")","",")")),
        ("${CC}",   ("${","CC","}")),
        ("$@",      ("$", "@",)),
        ("$<",      ("$", "<",)),
        ("$F",      ("$","F",)),
        ("$F",      ("$","F",)),
        ("$Ff",      ("$","F","f",)),
        ("$F$f",      ("$","F","$","f",)),
        ("$F$f$",      ("$$","$","F","$","f","$$",)),
        ("$($($(FOO)))",    ("$(","","$(","","$(","FOO",")","",")","",")")),
        ("$($($(FOO)a)b)c", ("$(","","$(","","$(","FOO",")","a",")","b",")")),
        ("$(a$(b$(FOO)a)b)c", ("$(","a","$(","b","$(","FOO",")","a",")","b",")")),
        ("$($($F)))",       ("$(","","$(","","$","F","",")","",")","",")")),
        ("$($($Fqq)))",     ("$(","","$(","","$","F","qq",")","",")","",")")),
        ("$(foo   )",       ("$(","foo   ",")")),
        ("$(info this is an info message)",     ("$(","info this is an info message",")")),
        ("$(error this is an error message)",   ("$(","error this is an error message",")")),
        ("$(findstring a,a b c)",               ("$(","findstring a,a b c",")")),
        ("$(patsubst %.c,%.o,x.c.c bar.c)",     ("$(","patsubst %.c,%.o,x.c.c bar.c",")")),
        ("$(filter %.c %.s,$(sources))",        ("$(",
                                                    "filter %.c %.s,",
                                                    "$(",
                                                    "sources",
                                                    ")",
                                                    "",
                                                    ")",
                                                )),
        ("$(objects:.o=.c)",        ("$(","objects:.o=.c",")",)),
        ("$(filter-out $(mains),$(objects))",   ("$(","filter-out ","$(","mains",")",",","$(","objects",")","",")","",")")),
        ("$(subst :, ,$(VPATH))",   ("$(","subst :, ,","$(","VPATH",")","",")")), # spaces are significant!
#        ("$(foo)$(\#)bar=thisisanother\#testtesttest", ("$(","k
        ("$(info = # foo#foo foo#foo foo#foo ###=# foo#foo foo#foo foo#foo ###)",
          ("$(","info = # foo#foo foo#foo foo#foo ###=# foo#foo foo#foo foo#foo ###",")")),
    )

#    run_tests_list( variable_ref_tests, tokenize_variable_ref )
    
    for test in variable_ref_tests : 
        s,v = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_variable_ref(my_iter)
        print( "tokens={0}".format(str(tokens)) )
        print("\n")

    # this should fail
#    print( "var={0}".format(tokenize_variable_ref(ScannerIterator("$(CC"))) )

if __name__=='__main__':
    run()

