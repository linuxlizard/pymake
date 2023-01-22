# SPDX-License-Identifier: GPL-2.0

# test parsing a whole rule
#
# XXX work in progress!

from pymake.scanner import ScannerIterator
import pymake.source as source
from pymake.tokenizer import tokenize_statement
import pymake.symbolmk as symbolmk
import pymake.symtablemk as symtablemk
import pymake.vline as vline

def test_simple_rule():
    s = """\
foo:
	@echo foo
"""
    # kind of a ridiculous amount of setup just to parse a rule...
    src = source.SourceString(s)
    src.load()
    line_scanner = ScannerIterator(src.file_lines, src.name)
    vline_iter = vline.get_vline(src.name, line_scanner)

    virt_line = next(vline_iter)
    vchar_scanner = iter(virt_line)
    statement = tokenize_statement(vchar_scanner)
    assert isinstance(statement, symbolmk.RuleExpression)


def test_circular_dependency():
    s = """\
foo: foo
	@echo foo
"""
    # warning: Circular foo <- foo dependency dropped

