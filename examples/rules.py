# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole david.poole@ericsson.com
#
# Demo parsing a rule
#
# run with:
# PYTHONPATH=. python3 examples/rules.py
#
# davep 20241129

import logging

import pymake.source as source
import pymake.vline as vline
import pymake.tokenizer as tokenizer
from pymake.scanner import ScannerIterator

from gnu_make import run_gnu_make, debug_save

logger = logging.getLogger("pymake")

test_file="""
one:

two : $(TWO)

three : ; echo foo

four : FOO:=BAR
four:

five: FOO?=BAR
five : /dev/null /dev/zero

# double colon rule
six::

   seven ::

$(eight):$(nine)$(ten)$(eleven)

# static pattern rule (straight from GNU Make manual)
# Not Implemented Yet
# $(objects): %.o: %.c

# Can have a var assignment with what looks like a a recipe statement following.
# Except if there is an assignment statement, the ; is not a recipe but is
# appended back to the assignment. The following launches a shell 
# executing 'ls ; echo'
twelve : FOO!=ls ; echo $(FOO)
twelve : ; @echo found $(words $(FOO)) files

# NotImplementedError
#thirteen&:

thirteen& : foo

fourteen|:

fifteen? : bar?

$$sixteen$$ : $$bar$$

"""

error_cases = [
    """
    # Not a valid assignment statement.
    # So a dependency on '=' ?
    # NOPE! "empty variable name"  The '=' is still treated as assignment.
    thirteen :: =
    """,

]

def main():
    name = "rule-recipe-block-test"

    src = source.SourceString(test_file)
    src.load()

    debug_save(src.file_lines)

    # verify everything works in GNU Make
    run_gnu_make(src.file_lines)

    # iterator across all actual lines of the makefile
    # (supports pushback)
    line_scanner = ScannerIterator(src.file_lines, src.name)

    # iterator across "virtual" lines which handles the line continuation
    # (backslash)
    vline_iter = vline.get_vline(name, line_scanner)

    for virt_line in vline_iter:
        vchar_scanner = iter(virt_line)
        lhs = tokenizer.tokenize_rule(vchar_scanner)
        assert lhs is not None
        token_list, rule_op = lhs
        print(token_list, rule_op)
        print("".join([str(t) for t in token_list]))

        rhs = tokenizer.tokenize_rule_RHS(vchar_scanner)
        print("rhs=",rhs)

        # anything left must be pointing to the start of a recipe
        if vchar_scanner.remain():
            vchar = vchar_scanner.lookahead()
            assert vchar.char == ';', vchar.char
            recipe = tokenizer.tokenize_recipe(vchar_scanner)
            assert recipe, recipe
            print("recipe=",recipe)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
#    logging.getLogger("pymake.tokenize").setLevel(level=logging.DEBUG)
    main()

