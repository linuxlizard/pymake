import symbol
from symbol import Symbol
from symtable import SymbolTable
from functions_str import *
from functions_str import strings_evaluate, StringFnEval

class StringToken(Symbol):
    def __init__(self, s):
        self.string = s

    def eval(self, symbol_table):
        return [self.string]

class StringFnMock(StringFnEval):
    def __init__(self, token_list):
        self.token_list = token_list

def test_words():
    symtable = SymbolTable()
    w = Words([StringToken("foo bar baz")])
    print(w)
    assert w.eval(symtable) == ['3']

def test_strings_evaluate():
    # I've confused myself at the difference between my strings_evaluate() and
    # StringFnEval.evaluate()

    symtable = SymbolTable()
    tokens = [StringToken("a b c")]
#    tokens = [StringToken("a b c"), [StringToken("foo bar baz")]]
    s = strings_evaluate(tokens, symtable)
    print(s)

    seval = StringFnMock(tokens)
    print(list(seval.evaluate(symtable)))

    # ['abc']
    # ['a', 'b', 'c']
    tokens = [StringToken("a"), StringToken("b"), StringToken("c")]
    print(strings_evaluate(tokens, symtable))
    print(list(StringFnMock(tokens).evaluate(symtable)))

    # ['a', 'b', 'c']
    # ['a', 'b', 'c']
    tokens = [StringToken("a"), StringToken(" "), StringToken("b"), StringToken(" "), StringToken("c")]
    print(strings_evaluate(tokens, symtable))
    print(list(StringFnMock(tokens).evaluate(symtable)))

if __name__ == '__main__':
    test_strings_evaluate()

