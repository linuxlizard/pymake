#!/usr/bin/env python3

# Run all the regression tests.
# davep 27-Sep-2014

import sys

import assign_test
import internals_test
import recipe_test
import rule_test
import statement_test
import varref_test

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")


def run_tests_list(tests_list,tokenizer):
    for test in tests_list :
        print("test={0}".format(test))
        s,result = test
        print("s={0}".format(s))
        my_iter = ScannerIterator(s)
        tokens = [ t for t in tokenizer(my_iter)] 
        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

        assert len(tokens)==len(result), (len(tokens),len(result))

        for v in zip(tokens,result):
            print("\"{0}\" \"{1}\"".format(v[0].string,v[1]))
            assert  v[0].string==v[1], v

def run_all_tests():
    assign_test.run()
    internals_test.run()
    recipe_test.run()
    rule_test.run()
    varref_test.run()
    statement_test.run()

if __name__=='__main__':
    run_all_tests()

