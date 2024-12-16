# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 David Poole davep@mbuf.com david.poole@ericsson.com


# I tried hard to make the parser context free but that's not going to work. 
# How <tab> (cmd prefix) is interpretted depends on whether a Rule has been
# seen or not. A line with <tab> is treated as a regular line if a Rule
# hasn't been seen yet. Once a Rule has been seen, a <tab> line *might* be
# a Recipe. So need to preserve context across parse_vline calls. 

class ParseState:
    def __init__(self):
        self.rules = 0

