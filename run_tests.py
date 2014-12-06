#!/usr/bin/env python3

# Run all the regression tests.
# davep 27-Sep-2014
#
# Moved most responsibility to run_tests.sh
# davep 26-Nov-2014

import sys
import subprocess
import tempfile

from pymake import *
import pymake
from vline import VirtualLine
import hexdump
from printable import printable_string

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

def runlocals(locals):
    # Run all functions named "testNN". Created to be imported into a script
    # and will run all functions named test1(), test2(), ... testN()
    import itertools
    counter = itertools.count(1)
    for i in counter :
        f = "test{0}".format(i)
        if not f in locals:
            break
        print("{0}()".format(f))
        locals[f]()

def run_makefile_string(in_string,expected_string):
    # parse a Makefile from a string. 
    # Compare resulting makefile to expected string.
    makefile = pymake.parse_makefile_string(in_string)
    m = makefile.makefile()

    print("# start makefile")
    print(m)
    print("# end makefile")

    print(hexdump.dump(in_string,16),end="")
    print(hexdump.dump(expected_string,16),end="")
    print(hexdump.dump(m,16),end="")

    print("m=\"{0}\"".format(printable_string(m)))
    print("e=\"{0}\"".format(printable_string(expected_string)))
    assert m==expected_string

    # round trip
    expr = str(makefile)
    print(expr)
    m2 = eval(expr).makefile()
    print(m2)
    assert m2==expected_string,m2


