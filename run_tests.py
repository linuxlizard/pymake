#!/usr/bin/env python3

# Run all the regression tests.
# davep 27-Sep-2014

import sys
import subprocess
import tempfile

import pymake
from vline import VirtualLine

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

def run_tests_list(tests_list,tokenizer):
    for idx,test in enumerate(tests_list) :
        s,validate = test
        print("test={0}".format(test))

        file_lines = s.split("\n")
        lines = [ line+"\n" for line in file_lines ]
        # if empty line at end, kill it (supposed to be cleaned out of vline
        # before sent to parser)
        if lines[-1]=='\n':
            lines = lines[:-1]
        print( "split={0}".format(s.split("\n")))
        print( "lines={0} len={1}".format(lines,len(lines)),end="")

        vline = VirtualLine(lines,idx)
        my_iter = iter(vline) 

        print("vline={0}".format(str(vline)))
        tokens = tokenizer(my_iter)
        print( "  tokens={0}".format(str(tokens)) )
        print( "validate={0}".format(str(validate)) )

        assert tokens==validate, (idx,)

        print( tokens.makefile() )
        print("\n")

def run_all_tests():
    import assign_test
    import internals_test
    import recipe_test
    import rule_test
    import statement_test
    import varref_test
    import comment_test

    assign_test.run()
    internals_test.run()
    recipe_test.run()
    rule_test.run()
    varref_test.run()
    statement_test.run()
    comment_test.run()

def directives_test(): 
    # Build makefiles with directives as rule and as assignment statement.
    # Run make. List the ones that succeed, fail.

    # GNU Make likely parses Makefiles looking for directives by tokenizing by
    # the space. 
    #   ifdef:      <--- allowed
    #   ifdef :     <--- parse fail
    #
#    makefile_str = "{0}=foo\nall: ; @echo target=$@ $$$$\n"
    makefile_str = "{0} = foo\nall: ; @echo target=$@ $$$$\n"
#    makefile_str = "{0} : ; @echo target=$@ $$$$\n"
#    makefile_str = "{0} : ; @echo target=$@ $$$$\n"

    make = "/usr/bin/make"

    failed = {}
    passed = {}

    for target in pymake.directive : 

        with tempfile.NamedTemporaryFile("w",prefix="./",delete=True) as outfile : 
            outfile.write( makefile_str.format(target) );
            outfile.flush()
            
#            print("target={0}".format(target))
            
            cmd = ( "/bin/cat", outfile.name )
            output = subprocess.check_output( cmd, shell=False )
#            print("{0}".format(output))

            cmd = ( make, "-f", outfile.name )
            try : 
                output = subprocess.check_output( cmd, stderr=subprocess.STDOUT, shell=False )
#                print("{0}".format(output))
                passed[target] = output
            except subprocess.CalledProcessError as err:
                failed[ target ] = err.output
#                print("err={0}".format(err))
                pass

    for f in failed : 
        print("failed {0} {1}".format(f,failed[f]))
    for s in passed:
        print("passed {0} {1}".format(s,passed[s]))

if __name__=='__main__':
#    directives_test()
    run_all_tests()

