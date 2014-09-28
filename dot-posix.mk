# .POSIX changes some of make's behaviors
#
# 28-sep-2014

$(error TODO)

.POSIX

# 3.1.1 Splitting Long Lines
#  "Outside of recipe lines, backslash/newlines are converted into a single
#  space character. Once that is done, all whitespace around the
#  backslash/newline is condensed into a single space: this includes all
#  whitespace preceding the backslash, all whitespace at the beginning of the
#  line after the backslash/newline, and any consecutive backslash/newline
#  combinations."
#
#  "If the .POSIX special target is defined then backslash/newline handling is
#  modified slightly to conform to POSIX.2: first, whitespace preceding a
#  backslash is not removed and second, consecutive backslash/newlines are not
#  condensed."
#
more-fun-in-assign\
=           \
    the     \
    leading \
    and     \
    trailing\
    white   \
    space   \
    should  \
    be      \
    eliminated\
    \
    \
    \
    including \
    \
    \
    blank\
    \
    \
    lines
