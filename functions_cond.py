# functions for conditionals

from functions_base import Function, FunctionWithArguments

__all__ = [ "AndClass", "IfClass", "OrClass" ]

class AndClass(FunctionWithArguments):
    name = "and"
    num_args = -1 # no max args

    # "Each argument is expanded, in order. If an argument expands to an empty
    # string the processing stops and the result of the expansion is the empty
    # string. If all arguments expand to a non-empty string then the result of
    # the expansion is the expansion of the last argument." -- gnu_make.pdf
    def eval(self, symbol_table):
#        breakpoint()
        for arg in self.args:
            result = "".join([a.eval(symbol_table) for a in arg])
            if not len(result):
                return ""
        return result


class IfClass(FunctionWithArguments):
    name = "if"
    # required args 2, optional args 3,
    # anything > 3 lumped together with the 3rd
    # (min,max)
    num_args = 3

    def eval(self, symbol_table):
        result = "".join([a.eval(symbol_table) for a in self.args[0]])
        if len(result):
            return "".join([a.eval(symbol_table) for a in self.args[1]])
        else:
            # args[3] should be Literal(",")
#            assert len(self.token_list[3].string)==1 and self.token_list[3].string[0].char == ','
#            breakpoint()
            return "".join([a.eval(symbol_table) for args in self.args[2:] for a in args])

class OrClass(FunctionWithArguments):
    name = "or"
    num_args = -1  # no max

    # "Each argument is expanded, in order. If an argument expands to a
    # non-empty string the processing stops and the result of the expansion is
    # that string." -- gnu_make.pdf
    def eval(self, symbol_table):
        for arg in self.args:
            result = "".join([a.eval(symbol_table) for a in arg])
            if len(result):
                return result
        return ""

