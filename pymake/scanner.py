# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2024 David Poole davep@mbuf.com david.poole@ericsson.com
#
# Scanner (as in scanner for tokenizer/parser)
# Needed an iterator that supports pushback and state save/restore.
# (fancy shmancy https://en.wikipedia.org/wiki/Pushdown_automaton)

import string
import logging

logger = logging.getLogger("pymake.scanner")

class ScannerIterator(object):
    # string iterator that allows look ahead and push back
    # can also push/pop state (for deep lookaheads)
    def __init__(self, data, name):
        logger.debug("ScannerIterator datalen=%d", len(data))
        self.data = data
        self.filename = name
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
        return self.data[self.idx]

    def pushback(self):
        if self.idx <= 0 :
            raise StopIteration
        self.idx -= 1

    def push_state(self):
        self.state_stack.append(self.idx)

    def pop_state(self):
        self.idx = self.state_stack.pop()

    def clear_state(self):
        # remove previous state pushed but do not restore it
        # (we pushed but decided we didn't need to pop)
        _ = self.state_stack.pop()

    def remain(self):
        # Test/debug method. Return what remains of the data.
        return self.data[self.idx:]

    def is_empty(self):
        return self.idx >= self.max_idx

    def is_starting(self):
        return self.idx == 0

    def get_pos(self):
        return self.data[self.idx].get_pos()
