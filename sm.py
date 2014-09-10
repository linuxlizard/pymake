#!/usr/bin/env python3

# Parse GNU Make with state machine. 
# Trying hand crafted state machines over pyparsing. GNU Make has very strange
# rules around whitespace.
#
# davep 09-sep-2014

whitespace = set( ' \t\r\n' )

class ParseError(Exception):
    pass

def comment(string):
    state_start = 1
    state_eat_comment = 2
    state_escape = 3

    state = state_start
    for c in string : 
#        print("c={0} state={1}".format(c,state))
        if state==state_start:
            if c=='#':
                state = state_eat_comment
            elif c=='\\':
                yield c
                state = state_escape
            else:
                yield c
        elif state==state_eat_comment:
            if c=='\n' :
                yield c
                state = state_start
            # otherwise char is eaten
        elif state==state_escape:
            yield c
            state = state_start
        else:
            assert 0, state

def eatwhite(string):
    # eat all whitespace (testing characters + sets)
    for c in string:
        if not c in whitespace:
            yield c

def parse_variable_ref(string):
    
    state_start = 1
    state_dollar = 2
    state_parsing = 3

    state = state_start
    token = ""

    print( "state={0}".format(state))

    for c in string : 
#        print("c={0} state={1}".format(c,state))
        if state==state_start:
            if c=='$':
                state=state_dollar
        elif state==state_dollar:
            # looking for '(' or '$' or some char
            if c=='(':
                state = state_parsing
                yield "$("
            elif c=='$':
                # literal "$$"
                yield "$$"
                return None
            elif not c in whitespace :
                # single letter variable, e.g., $@ $x $_ etc.
                token += c
                yield "$"
                yield token
                return None
        elif state==state_parsing:
            if c==')':
                yield token
#                print("ending )")
                yield ")"
                return None
            elif c=='$':
#                print("nested!")
                # nested expression!  :-O
                string.pushback()
                # http://stackoverflow.com/questions/8407760/python-how-to-make-a-recursive-generator-function
                if 1 : 
                    for t in parse_variable_ref(string):
                        yield t
                else :
                    # python 3.3 and above
                    yield from parse_variable_ref(string)
            else:
                token += c

    raise ParseError()

class ScannerIterator(object):
    # string iterator that allows look ahead and push back
    def __init__(self,string):
        self.string = string
        self.idx = 0
        self.max_idx = len(self.string)

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx >= self.max_idx:
            raise StopIteration
        self.idx += 1
        return self.string[self.idx-1]

    def lookahead(self):
        if self.idx >= self.max_idx:
            raise StopIteration
        return self.string[self.idx]

    def pushback(self):
        if self.idx <= 0 :
            raise StopIteration
        self.idx -= 1

def parse(infilename):
    infile = open(infilename)
    all_lines = infile.readlines()
    infile.close()

    s = "".join(all_lines)
    
    my_iter = ScannerIterator(s)

    new_makefile = "".join( [ c for c in eatwhite(comment(my_iter)) ] )
    print(new_makefile)

#    for c in comment(s):
#        print(c,end="")

def main():
    import sys
    for infilename in sys.argv[1:]:
        parse(infilename)

    expression_tests = ( 
        "$$", 
        "$(CC)", 
#        "${CC}", 
        "$@", "$<", "$F", "$($($(FOO)))", "$($($F)))", 
        "$(foo   )",
        "$(info this is an info message)",
        "$(error this is an error message)",
        "$(findstring a,a b c)",
        "$(patsubst %.c,%.o,x.c.c bar.c)",
        "$(filter %.c %.s,$(sources))",
        "$(objects:.o=.c)",
        "$(filter-out $(mains),$(objects))",
        "$(subst :, ,$(VPATH))",  # spaces are significant!
    )
    for s in expression_tests :
        print("s={0}".format(s))
        my_iter = ScannerIterator(s)
        print( "var={0}".format([ t for t in parse_variable_ref(my_iter)] ) )

    # this should fail
#    print( "var={0}".format(parse_variable_ref(ScannerIterator("$(CC"))) )

if __name__=='__main__':
    main()

