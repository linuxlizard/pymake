#!/usr/bin/env python3

# "Virtual Block" -- a 2D array of characters with visible/not visible
# attribute.
#
# Created to handle joining backslash'd lines together for the tokenizer. Has
# evolved into something that will be useful for the makefile View.
#
# davep 01-Oct-2014

import sys
import itertools
import logging

logger = logging.getLogger("pymake.vline")

_debug = True

import pymake.hexdump as hexdump
from pymake.scanner import ScannerIterator
from pymake.printable import printable_char, printable_string
from pymake.constants import eol, backslash, whitespace, recipe_prefix

# indices into VirtualLine's characters' position.
VCHAR_ROW = 0
VCHAR_COL = 1


def is_line_continuation(line):
    # does this line end with "\" + eol?
    # (hiding in own function so can eventually handle "\"+CR+LF)

    # if we don't end in an EOL, definitely not a continuation
    if len(line) and not line[-1] in eol:
        return False

    # back up past the EOL then verify the next char is \
    pos = len(line)-1
    while pos >= 0 and line[pos] in eol:
        pos -= 1
    return pos >= 0 and line[pos] == backslash

def vchars_debug_string(vchar_list):
    """Utility function to debug dump an array of vchars"""
    return " ".join([str((vc.char,str(vc.pos))) for vc in vchar_list])

def validate_vchars(vchar_list):
    if not _debug:
        return            

    # Super paranoid check on the validity of every character in every token.
    # Verify the position of every character in the characters' filenames.

    infile = None
    infilename = None
    lines_list = []
    for vchar in vchar_list:
#        logger.debug("validating \"%s\" @ %d,%d %s %r", vchar.printable(), vchar.row, vchar.col, vchar.filename, vchar.hide)

        if vchar.filename == "/dev/null":
            # test/debug code ; ignore
            continue

        if infilename is None:
            infilename = vchar.filename

        if infilename != vchar.filename:
            # filename has changed so open a new file    
            infilename = vchar.filename
            infile.close() if infile else None
            infile = None

        if infile is None:
            infile = open(infilename,'r')
            lines_list = infile.readlines()

        try:
            file_char = lines_list[vchar.row][vchar.col]
        except IndexError:
            # this is bad, very bad
            breakpoint()
            raise

        # VChar underlying char must match the file. But...
        # I replace '\' line continuation char with ' ' in the string.
        # Is this original character a '\' that's been replaced?
        # (see also VChar.set_backslash())
        if file_char != vchar.char and file_char != backslash:
            # this is bad, very bad
            breakpoint()

            assert file_char != backslash and file_char == vchar.char, (file_char,vchar.char)

    if infile:
        infile.close()

#def validate_vchars_hide(vchar_list):
#    for vchar in vchar_list:
#        
#        if vchar.char in eol:
#            if not vchar.hide:
#                breakpoint()
#            assert vchar.hide, (printable_char(vchar.char),vchar.pos)

# using a class for the virtual char so can interchange string with VirtualLine
# in ScannerIterator
class VChar(object):
    def __init__(self, char, pos, filename):
        # ha ha python type checking
        assert len(char)==1, len(char)
        assert isinstance((pos), type(())), type(pos)
        assert len(pos) == 2, pos

        self._char = char
        # VCHAR_ROW, VCHAR_COL index into pos
        self._pos = pos

        # show/hide this char (e.g., hide if in a comment or backslash with
        # weird whitespace)
        self.hide = False

        self.filename = filename

    @property
    def pos(self): 
        return self._pos

    @property
    def char(self):
        return self._char

    @property
    def row(self):
        return self._pos[VCHAR_ROW]

    @property
    def col(self):
        return self._pos[VCHAR_COL]

    @property
    def linenumber(self):
        """ one-based line number (vs the zero-based row/col)"""
        return self.pos[VCHAR_ROW]+1

    def get_pos(self):
        return self.filename, self._pos

    def __str__(self):
        return self.char

    def printable(self):
        return printable_char(self.char)

    def set_backslash(self):
        # This is a weird wart on the whole thing. A series of lines joined
        # together with a '\' are treated as a single line (the VirtualLine).
        # The VirutalLine is given as a single unbroken line, terminated with a
        # single '\n', to the scanner and parser. In GNU Make, the separate
        # lines are joined by a space (0x20). 
        #
        # Section 3.1.1  Splitting Long Lines.  
        # "Outside of recipe lines, backslash/newlines are converted into a single space character.
        # Once that is done, all whitespace around the backslash/newline is condensed into a single
        # space: this includes all whitespace preceding the backslash, all whitespace at the beginning
        # of the line after the backslash/newline, and any consecutive backslash/newline combina-
        # tions."  -- GNU Make 4.3 Jan 2020
        #
        # In VirtualLine, I'm replacing the
        # '\' with a space so the array of individual lines can be joined
        # together with that space.
        # The upper level code must see a space, not the backslash. But the
        # sanity validation code needs to see a '\' in order to match the
        # source file.
        self._char = ' '


class VCharString(object):
    # davep 24-Apr-2016 ;  
    # container of VChar; quack like a Python string
    # Symbols contain a VCharString contains VChar contains filename, position, real char
    def __init__(self, arg=None):
        self.chars = list(arg) if arg else []
        # verify we have VChar
        if self.chars:
            self.chars[0].pos

    def __str__(self):
        return "".join([str(c) for c in self.chars if not c.hide])

    def __add__(self, vchar):
        assert vchar.pos
        assert vchar.filename
        self.chars.append(vchar)
        return self

    def __len__(self):
        return len(self.chars)

    def __getitem__(self, idx):
        return self.chars[idx]

    @classmethod
    def from_string(cls, python_string):
        # make a VCharString from a regular python string (mostly used with
        # testing so the positions and filename will be nonsense)
        return cls([VChar(c, (0,0), "/dev/null") for c in python_string])

    def validate(self):
        validate_vchars(self.chars)

    def printable_str(self):
        # build string from the visible characters.
        # see also printable_str() in VirtualLine
        s = "".join([printable_char(vchar.char) for vchar in self.chars if not vchar.hide]) 
        return s

    def get_pos(self):
        # XXX what about empty VCharString ?
        return self.chars[0].filename, self.chars[0].pos

class VirtualLine(object):
    def __init__(self, phys_lines_list, starting_pos, filename):
        logger.debug("VirtualLine pos=%r filename=%s", starting_pos, filename)
        logger.debug("lines=%s", phys_lines_list)

        # ha-ha type checking
        int(starting_pos[0]), int(starting_pos[1])

        # need an array of strings (2-D array of characters)
        assert isinstance(phys_lines_list, list)
        for p in phys_lines_list:
            assert isinstance(p, str), type(p)

        assert isinstance(starting_pos, type(())), type(starting_pos)

        # catch problem code
        assert len(filename), (type(filename), filename)

        # check for integer
#        assert starts_at_file_line+1 >= 0, starts_at_file_line

        # where do I come from?
        self.filename = filename

        # save a pristine copy of the original list
        self.phys_lines = phys_lines_list

        # this is where this line blob started in the original source file
        self.starting_pos = starting_pos

        # create a 2-d array of all the characters with their position in
        # the file
        self.virt_chars = []
        self._make_virtual_line()

        # Based on the \ line continuation rules, collapse 2-D array into a new
        # 1-D "virtual" array of characters that will be sent to the tokenizer.
        self._collapse_virtual_line()

    def _make_virtual_line(self):
        # Create a 2-D array of VChar from our 2-D array (array of strings).
        #
        # The new 2-D array will be the characters with their row, col in the
        # 2-D array.
        starting_row = self.starting_pos[VCHAR_ROW]
        starting_col = self.starting_pos[VCHAR_COL]
        for row_idx, line in enumerate(self.phys_lines):
            vchar_list = []
            for col_idx, char in enumerate(line):
                # char is the original character
                # pos is the (row, col) of the char in the file
                pos = (row_idx+starting_row, 
                       col_idx+starting_col)
                vchar = VChar(char, pos, self.filename)
#                if _debug:
#                    print("vchar=%r at %r" % (vchar.char, vchar.get_pos()))
                vchar_list.append(vchar)
            # reset the column back to zero since we're on a new line
            starting_col = 0
            self.virt_chars.append(vchar_list)

    def _collapse_virtual_line(self):
        # Section 3.1.1  Splitting Long Lines.  
        # "Outside of recipe lines, backslash/newlines are converted into a single space character.
        # Once that is done, all whitespace around the backslash/newline is condensed into a single
        # space: this includes all whitespace preceding the backslash, all whitespace at the beginning
        # of the line after the backslash/newline, and any consecutive backslash/newline combina-
        # tions."  -- GNU Make 4.3 Jan 2020
        #
        # collapse continuation lines according to the whitepace rules around
        # the backslash (The rules will change if .POSIX is enabled)
        # TODO .POSIX support

        # if only a single line, don't bother
        if len(self.phys_lines)==1 :
            assert not is_line_continuation(self.phys_lines[0]), self.phys_lines[0]
            return

        # for each line in our virtual lines:
        # kill the eol and whitepace on both sides of \
        # kill empty lines
        #
        # For example:
        # """this \
        #      is      \
        #       a\
        #         \
        #    test
        # """
        # becomes "this is a test"
        #
        # Whitespace before and after each backslash joined line is maintained.
        # Whitespace between tokens in the line is maintained.
        #
        #    vv---- leading spaces preserved
        # """  this\
        #   is     a     \
        #   test  
        # """   ^^-- trailing spaces preserved
        # becomes "   this is     a test  "

        def clean_front(row):
            for vchar in row:
                if not vchar.char in whitespace:
                    break
                vchar.hide = True

        def clean_back(row):
            assert row[-1].char in eol
            assert row[-2].char == backslash

#            print("hide c=%r at %r" % (row[-1].char, row[-1].get_pos()))
            row[-1].hide = True

            # we will decide what to do with the backslash after we've checked
            # for an empty line

            # -1 to convert from length to index
            # -2 to skip the trailing backslash+eol
            idx = len(row)-1-2

            if idx < 0:
                # we have a very corner case of a line of just backslash+eol
                # for example:
                # \\\n
                row[-2].hide = True
                return

            # In this loop, we check for entirely hidden lines (all whitespace
            # or an empty line, (but still joined by backslashes)). 
            # For example: 
            #
            # foo=\\\n
            #    \\\n
            #    \\\n
            #    bar\n
            # becomes "foo= bar\n"
            #
            # foo=\\\n
            # \\\n
            # \\\n
            # bar\n
            # also becomes "foo= bar\n"

            while idx >= 0 and row[idx].char in whitespace:
                if row[idx].hide:
                    # we've bumped into a whitespace already hidden by clean_front()
                    # so this entire line must be hidden
                    row[-2].hide = True
                    return
                    
                row[idx].hide = True
                idx -= 1

#            print("backslash c=%r at %r" % (row[-2].char, row[-2].get_pos()))
            row[-2].set_backslash()
        # end of clean_back()

        # leading spaces on first line are preserved
        clean_back(self.virt_chars[0])

        rowidx = 1
        while rowidx < len(self.virt_chars)-1:
            clean_front(self.virt_chars[rowidx])
            clean_back(self.virt_chars[rowidx])
            rowidx += 1

        # trailing spaces on last line are preserved
        clean_front(self.virt_chars[rowidx])

    def __str__(self):
        # build string from the visible characters
        lines = []
        for row in self.virt_chars:
            s = "".join([vchar.char for vchar in row if not vchar.hide]) 
            lines.append(s)

        return "".join(lines)

    def __iter__(self):
        # This iterator we will feed the characters that are still visible to
        # the tokenizer. Using ScannerIterator so we have pushback. The
        # itertools.chain() joins all the virt_lines together into one
        # contiguous array
        virt_iterator = ScannerIterator([vchar for vchar in itertools.chain(*self.virt_chars) if not vchar.hide], self.filename)
        return virt_iterator

    def get_pos(self):
        return (self.filename,
            # position of this line (in a file) is the position of the first char
            # of the first line
            self.virt_chars[0][0].pos)

    def get_phys_line(self):
        # rebuild a single physical line (needed when tokenizing recipes)
        return "".join(self.phys_lines)

    def python(self):
        # Return a Python expression representing this virtual line.
        # Used in str() methods from Symbol class hierarchy to round trip the
        # code.
        s = "VirtualLine(["
        s += ", ".join( ["\"{0}\"".format(printable_string(p)) for p in self.phys_lines] )
        s += "], {}, {})".format(self.filename, self.starting_pos)
        return s

    def get_code(self):
        return { "filename": self.filename,
                 "src" : self.phys_lines,
                 "": self.starting_pos}

    def validate(self):
        for row in self.virt_chars:
            validate_vchars(row)

class RecipeVirtualLine(VirtualLine):
    # This is a block containing recipe(s). Don't collapse around backslashes.
    # Different rules apply.
    #
    # 5.1.1 Splitting Recipe Lines
    #
    # "... backslash/newline pairs are not removed from the recipe. Both the
    # backslash and the newline characters are preserved and passed to the shell."
    #
    # If the first character of the next line after the backslash/newline is the
    # recipe prefix character (a tab by default [...]) then that character (and
    # only that character) is removed. Whitespace is never added to the recipe."
    #
    # -- GNU Make 4.3 Jan 2020
    #
    # Since we've already broken the file lines into an array of characters, we
    # just need to peek/poke the first and last chars of those arrays.
    #
    def _collapse_virtual_line(self):
        # reminder: self.virt_chars is an array of arrays of vchars
        # outer array contains lines
        # inner array contains the characters in the line

        # don't modifiy first row 
        row_iter = iter(self.virt_chars)
        row = next(row_iter)

        # check the end of the line for backslash/newline
        while len(row) >= 2 and row[-1].char in eol and row[-2].char == backslash:
#            print("r pos=%r is backslash/eol" % (row[-1].get_pos(),))
            # move to next row (allow StopIteration to propagate which
            # would indicate a trailing backslash with no further recipe
            # which would indicate a parse failure)
            row = next(row_iter)

            # if first char of the next row is a tab (aka recipe_prefix)
            # then hide it
            if row[0].char == recipe_prefix:
#                print("r pos=%r hidden" % (row[0].get_pos(),))
                row[0].hide = True

def get_vline(filename, line_iter): 
    # GENERATOR
    #
    # line_iter is an ScannerIterator that supports pushback.
    # Iterates across an array of strings.
    #
    # The line_iter can also be passed around to other tokenizers (e.g., the
    # recipe tokenizer). So this function cannot assume it's the only line_iter
    # user.
    #
    # Each string should be terminated by an EOL.  Handle cases where line is
    # continued after the EOL by a \+EOL (backslash).

    logger.debug("get_vline filename=%s line_iter=%s", filename, line_iter)

    state_start = 1
    state_backslash = 2
    state_tokenize = 3
    
    starting_line_number = -1
    state = state_start 

    is_recipe_prefix = False

    # note! line_iter is shared with the caller.
    # Also can't use enumerate() because the line_iter will also be used inside
    # parse_recipes() and the idx can change with push_back
    for line in line_iter :
        logger.debug("get_vline line_num=%d state=%d", line_iter.idx, state)

        if state==state_start : 
            # line_iter.idx is the *next* line number counting from zero 
            starting_line_number = line_iter.idx-1

            if line[0] == recipe_prefix:
                is_recipe_prefix = True
            else:
                is_recipe_prefix = False

            start_line_stripped = line.strip()

            # ignore blank lines
            if len(start_line_stripped)==0:
                continue

            line_list = [ line ] 

            if is_line_continuation(line):
                # We found a line with trailing \+eol
                # We will start collecting the next lines until we see a line
                # that doesn't end with \+eol
                state = state_backslash
            else :
                # We found a single line of makefile. Tokenize!
                state = state_tokenize

        elif state==state_backslash : 
            line_list.append( line )
            if not is_line_continuation(line):
                # This is the last line of our continuation block. Create a
                # virtual block for this array of lines.
                state = state_tokenize

        else:
            # wtf?
            assert 0, state

        # Note the state machine falls through from the above state_start
        # and state_backslash handlers to this point. 

        if state==state_tokenize: 
            # is this a Makefile line comment?
            # (not a recipe line because comments are passed through to the shell)
            if not is_recipe_prefix and start_line_stripped.startswith("#") :
                # ignore the whole line
                state = state_start
                continue

            # make a virtual line (joins together backslashed lines into one
            # single line visible through a character by character iterator)
            if is_recipe_prefix:
                virt_line = RecipeVirtualLine(line_list, (starting_line_number,0), filename)
            else:
                virt_line = VirtualLine(line_list, (starting_line_number,0), filename)

            # get rid of the array so I will fail with None.append() if I wind
            # up in the wrong state
            del line_list 

            yield virt_line

            # start searching for a new line
            state = state_start

    return None

