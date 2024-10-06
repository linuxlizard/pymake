# SPDX-License-Identifier: GPL-2.0

# start of useful debugger tools
#
__all__ = [
    "get_line_number",
]

def get_line_number(o):
    # get_pos() returns tuple
    # [0] is filename, [1] is tuple (row, column)
    # Want the line number.
    return o.get_pos()[1][0]


