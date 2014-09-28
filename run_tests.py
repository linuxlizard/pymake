#!/usr/bin/env python3

# Run all the regression tests.
# davep 27-Sep-2014

import sys

from sm import ScannerIterator

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")


def run_tests_list(tests_list,tokenizer):
    for test in tests_list :
        s,validate = test
        print("test={0}".format(test))
        my_iter = ScannerIterator(s)

        tokens = tokenizer(my_iter)
        print( "  tokens={0}".format(str(tokens)) )
        print( "validate={0}".format(str(validate)) )

        assert tokens==validate

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

if __name__=='__main__':
    run_all_tests()

