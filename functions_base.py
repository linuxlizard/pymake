# top of the functions' class hierarchy

import logging

logger = logging.getLogger("pymake.functions")

from symbol import VarRef, Literal
from vline import VCharString, whitespace

class Function(VarRef):
    def __init__(self, args):
        logger.debug("function=%s args=%s", self.name, args)
        super().__init__(args)

    def makefile(self):
        s = "$(" + self.name + " "
        for t in self.token_list : 
            s += t.makefile()
        s += ")"
        return s

    def eval(self, symbol_table):
        return ""


class FunctionWithArguments(Function):
    min_args = 0
    max_args = 0

    def __init__(self, token_list):
        super().__init__(token_list)
        self.args = []
        self._parse_args()

        # Functions can have variable number of arguments but some functions
        # need a specific minimum number.
        #
        # check for proper num_args
        # [0]==min [1]==max ; min/max number of arguments
        # num_args is None 
        #
        # TODO need to handle min,max args like gnu make does
        # (rather than assuming fns have an exact number of arguments)

    def _parse_args(self):
        """Parse the token list into an array of arguments separated by literal commas."""
        logger.debug("parse_args \"%s\" at %r", self.name, self.get_pos())

        arg_idx = 0
        self.args = []

        # ugh
        start = True

#        for t in self.token_list:
#            print(f"_parse-args t={t}")

        def _save_arg(new_arg):
            # fn arguments are stored as an array self.args
            # but each arg itself can be an array of something (or even empty)
            try:
                self.args[arg_idx].append(new_arg)
            except IndexError:
                self.args.append( [ new_arg ] )

        # Walk along the token list looking for Literals which should contain
        # the commas.  Inside the literal(s), look for our comma(s).
        # Split the Literal into new Literals around the commas.
        # Preserve everything else as-is.
        token_iter = iter(self.token_list)
        for t in token_iter:
            # if not a literal string, then it's something we've already parsed
            # so no need to go through it again
            if not isinstance(t, Literal):
                # no touchy
#                print(f"save {t}")
                start = False
                _save_arg(t)
                continue

            # ugly special case: throw away leading spaces between the fn name
            # and the 1st argument. All other spaces need to be preserved. GNU
            # Make handles spaces in arguments differently depending on the fn.
            # For example, $(if) wants the spaces but the string fns will
            # discard them (split on the whitespace)

            # at this point, we have some sort of literal string that we have
            # to separately parse for commas to make a function argument list
            #
            # peek inside the literal for commas 
            lit = []
            vstr_iter = iter(t.string)
            for vchar in vstr_iter:
#                if start:
#                    breakpoint()

                if start and vchar.char in whitespace:
                    continue

                # FIXME yuk ; I hate one-time flags
                start = False

                # looking for commas separating the args
                if vchar.char != ',':
                    lit.append(vchar)
                    continue

                logger.debug("found comma idx=%d pos=%r", arg_idx, vchar.pos)
                if lit:
                    # save whatever we've seen so far (if anything)
                    new_arg = Literal(VCharString(lit))
                    _save_arg(new_arg)
                    lit = []
                arg_idx += 1

                if arg_idx+1 == self.num_args:
                    # Done. Have everything we need.
                    # consume the rest of this string
                    # (this will break from the inner loop)
                    remaining = list(vstr_iter)
                    if remaining:
                        new_arg = Literal(VCharString(remaining))
                        _save_arg(new_arg)

                    # consume the rest of the token stream
                    # (this will break from the outer loop)
                    new_arg = list(token_iter)
                    try:
                        self.args[arg_idx].extend(new_arg)
                    except IndexError:
                        self.args.append(new_arg)

            # verify we haven't left anything dangling
            if lit:
                new_arg = Literal(VCharString(lit))
                _save_arg(new_arg)

        # sanity checks
        for arg_list in self.args:
            for arg in arg_list:
#                print(f"arg={arg} at {arg.get_pos()}")
                arg.get_pos()

        # TODO catch improper arguments
#        if arg_idx+1 < self.num_args:
#            # TODO better error
#            errmsg = "found args=%d but needed=%d" % (arg_idx, self.num_args)
#            logger.error(errmsg)
#            raise ParseError(errmsg)

