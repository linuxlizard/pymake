#!/usr/bin/env python3

# Scanner (as in scanner for tokenizer/parser)
# Needed an iterator that supports pushback and state save/restore.
# (fancy shmancy https://en.wikipedia.org/wiki/Pushdown_automaton)

import sys
import string

# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

class ScannerIterator(object):
    # string iterator that allows look ahead and push back
    # can also push/pop state (for deep lookaheads)
    def __init__(self,data):
        self.data = data
        self.idx = 0
        self.max_idx = len(self.data)
        self.state_stack = []

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        if self.idx >= self.max_idx:
            raise StopIteration
        self.idx += 1
        return self.data[self.idx-1]

    def lookahead(self):
        if self.idx >= self.max_idx:
            return None
#        print("lookahead={0}".format(self.data[self.idx]))
        return self.data[self.idx]

    def pushback(self):
        if self.idx <= 0 :
            raise StopIteration
        self.idx -= 1

    def push_state(self):
        self.state_stack.append(self.idx)
#        print( "push stack=", self.state_stack )

    def pop_state(self):
#        print( "pop stack=", self.state_stack )
        self.idx = self.state_stack.pop()

    def remain(self):
        # Test/debug method. Return what remains of the data.
        return self.data[self.idx:]

    def stop(self):
        # truncate the iterator at the current position
        assert self.idx < self.max_idx, self.idx

        # kill anything after the current position
        self.data = self.data[:self.idx]
        self.max_idx = len(self.data)

    def lstrip(self):
        # strip left leading whitespace (like "".strip)
        try : 
            while str(self.data[self.idx]) in string.whitespace :
                self.next()
        except IndexError:
            raise StopIteration

        # allow chaining
        return self

    def eat(self,s):
        # consume a string from the leading part of the data
        # for example:  eat("hello") from "hello, world" will result in 
        # ", world"
        #
        # Requires the string be found in the data, like string's index method.
        # Requires the string start exactly at the current position.

        errmsg = "\"{0}\" not found in {1}".format(s,self)
        for c in s :
            if self.idx >= self.max_idx:
                # full substring not found so error!
                raise ValueError(errmsg)

            if str(self.data[self.idx]) == c :
                self.next()
            else :
                # full substring not found so error!
                raise ValueError(errmsg)

        # allow chaining
        return self

