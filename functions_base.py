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
    def __init__(self, token_list):
        super().__init__(token_list)
        self.args = []
        self._parse_args()

    def _parse_args(self):
        """Parse the token list into an array of arguments separated by literal commas."""
        logger.debug("parse_args \"%s\"", self.name)

        arg_idx = 0
        self.args = []

#        for t in self.token_list:
#            print(t)

        # Walk along the token list looking for Literals which should contain
        # the commas.  Inside the literal(s), look for our comma(s).
        # Split the Literal into new Literals around the commas.
        # Preserve everything else as-is.
        token_iter = iter(self.token_list)
        for t in token_iter:
            if not isinstance(t, Literal):
                # no touchy
#                print(f"save {t}")
                try:
                    self.args[arg_idx].append(t)
                except IndexError:
                    self.args.append( [ t ] )
                continue

            # peek inside the literal for commas 
            lit = []
            vstr_iter = iter(t.string)
            for vchar in vstr_iter:
                # looking for commas separating the args
                if vchar.char != ',':
                    # consume leading whitespace
                    if arg_idx == 0 and vchar.char in whitespace:
                        pass
                    else:
                        lit.append(vchar)
                    continue

                logger.debug("found comma idx=%d pos=%r", arg_idx, vchar.pos)
                if lit:
                    # save whatever we've seen so far (if anything)
                    new_arg = Literal(VCharString(lit))
                    try:
                        self.args[arg_idx].append(new_arg)
                    except IndexError:
                        self.args.append([new_arg])
                    lit = []
                arg_idx += 1

                if arg_idx+1 == self.num_args:
                    # Done. Have everything we need.
                    # consume the rest of this string
                    # (this will break from the inner loop)
                    remaining = list(vstr_iter)
                    if remaining:
                        new_arg = Literal(VCharString(remaining))
                        try:
                            self.args[arg_idx].append(new_arg)
                        except IndexError:
                            self.args.append([new_arg])

                    # consume the rest of the token stream
                    # (this will break from the outer loop)
                    new_arg = list(token_iter)
                    try:
                        self.args[arg_idx].extend(new_arg)
                    except IndexError:
                        self.args.append(new_arg)

        # sanity checks
#        breakpoint()
        for arg in self.args:
            for field in arg:
                field.get_pos()
#                print(f"arg={field} at {field.get_pos()}")

        if arg_idx+1 < self.num_args:
            # TODO better error
            errmsg = "found args=%d but needed=%d" % (arg_idx, self.num_args)
            logger.error(errmsg)
            raise ParseError(errmsg)

