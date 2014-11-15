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

import hexdump
from scanner import ScannerIterator

eol = set("\r\n")
# can't use string.whitespace because want to preserve line endings
whitespace = set( ' \t' )

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

def is_line_continuation(line):
    # does this line end with "\" + eol? 
    # (hiding in own function so can eventually handle "\"+CR+LF)
    
    # if we don't end in an EOL, definitely not a continuation
    if len(line) and not line[-1] in eol : 
        return False

    # back up past the EOL then verify the next char is \
    pos = len(line)-1
    while pos >=0 and line[pos] in eol : 
        pos -= 1
    return pos>=0 and line[pos]=='\\'

# indices into VirtualLine's characters' position.
VCHAR_ROW = 0
VCHAR_COL = 1

# using a class for the virtual char so can interchange string with VirtualLine
# in ScannerIterator
class VChar(object):
    def __init__(self,char,pos):
        self.vchar = { "char" : char, 
                       "pos"  : pos,
                       "hide" : False } 

    def __getitem__(self,key):
        return self.vchar[key]
    
    def __setitem__(self,key,value):
        self.vchar[key] = value

    def __str__(self):
        # created this class pretty much just for this method :-/
        return self.vchar["char"]

class VirtualLine(object):

    def __init__(self,phys_lines_list, starts_at_file_line ):
        # need an array of strings (2-D array of characters)
        assert type(phys_lines_list)==type([])

        # save a pristine copy of the original list 
        self.phys_lines = phys_lines_list

        # this is where this line blob started in the original source file
        self.starting_file_line = starts_at_file_line

        # create a single array of all the characters with their position in
        # the 2-d array
        self.make_virtual_line()

        # Based on the \ line continuation rules, collapse 2-D array into a new
        # 1-D "virtual" array of characters that will be sent to the tokenizer. 
        self.collapse_virtual_line()

    def make_virtual_line(self):
        # Create a 2-D array of vchar (hash) from our 2-D array (array of
        # strings).
        #
        # The new 2-D array will be the characters with their row,col in the
        # 2-D array. 

        self.virt_lines = []
        for row_idx,line in enumerate(self.phys_lines) : 
            vline = []
            for col_idx,char in enumerate(line):
                # char is the original character
                # pos is the (row,col) of the char in the file
                # hide indicates a hidden character (don't feed to the
                # tokenizer, don't highlight in View)
#                vchar = { "char" : char, 
#                          "pos"  : (row_idx+self.starting_file_line,col_idx),
#                          "hide" : False } 
                vchar = VChar(char,(row_idx+self.starting_file_line,col_idx))
                vline.append(vchar)
            self.virt_lines.append(vline)

    def collapse_virtual_line(self):
        # collapse continuation lines according to the whitepace rules around
        # the backslash (The rules will change if we're inside a recipe list or
        # if .POSIX is enabled or or or or ...)
        
        # if only a single line, don't bother
        if len(self.phys_lines)==1 : 
            assert not is_line_continuation(self.phys_lines[0]), self.phys_lines[0] 
            return

        row = 0

        # for each line in our virtual lines
        # kill the eol and whitepace on both sides of \
        # kill empty lines
        # replace \ with <space>
        #
        # For example:
        # """this \
        #      is \
        #       a \
        #         \
        #    test
        # """
        # becomes "this is a test"
        #
        while row < len(self.virt_lines)-1 : 
#            print("row={0} {1}".format(row, hexdump.dump(self.phys_lines[row],16)),end="")

            # start at eol
            col = len(self.virt_lines[row])-1

            # kill EOL
            assert self.virt_lines[row][col]["char"] in eol, (row,col,self.virt_lines[row][col]["char"])
            self.virt_lines[row][col]["hide"] = True
            col -= 1

            # replace \ with <space>
            assert self.virt_lines[row][col]["char"]=='\\', (row,col,self.virt_lines[row][col]["char"])
            self.virt_lines[row][col]["char"] = ' ' 

            # are we now a blank line?
            if self.virt_lines[row][col-1]["hide"] :
                self.virt_lines[row][col]["hide"] = True

            col -= 1

            # eat whitespace backwards
            while col >= 0 and self.virt_lines[row][col]["char"] in whitespace : 
                self.virt_lines[row][col]["hide"] = True
                col -= 1

            # eat whitespace forward on next line
            row += 1
            col = 0
            while col < len(self.virt_lines[row]) and self.virt_lines[row][col]["char"] in whitespace : 
                self.virt_lines[row][col]["hide"] = True
                col += 1

        # Last char of the last line should be an EOL. There should be no
        # backslash on this last line.
        col = len(self.virt_lines[row])-1
        assert self.virt_lines[row][col]["char"] in eol, (row,col,self.virt_lines[row][col]["char"])
        col -= 1
        assert self.virt_lines[row][col]["char"] != '\\', (row,col,self.virt_lines[row][col]["char"])

    def __str__(self):
        # build string from the visible characters
        i = itertools.chain(*self.virt_lines)
        return "".join( [ c["char"] for c in i if not c["hide"] ] )

    def __iter__(self):
        # This iterator we will feed the characters that are still visible to
        # the tokenizer. Using ScannerIterator so we have pushback. The
        # itertools.chain() joins all the virt_lines together into one
        # contiguous array
        self.virt_iterator = ScannerIterator( [ c for c in itertools.chain(*self.virt_lines) if not c["hide"] ] )
        setattr(self.virt_iterator,"starting_file_line",self.starting_file_line)
        return self.virt_iterator

    def truncate(self,truncate_pos):
        # Created to allow the parser to cut off a block at a token boundary.
        # Need to parse something like:
        # foo : bar ; baz 
        # into a rule and a recipe but we won't know where the rule ends and
        # the (maybe) recipes begin until we fully tokenize the rule.
        # foo : bar ; baz 
        #           ^-----truncate here
        # (Only need this rarely)

        def split_2d_array( splitme, row_to_split, col_to_split ):
            # splite a 2-D array (array of strings to be exact) into two
            # arrays. The character at the split point belows to 'below'.
            above = splitme[:row_to_split]
            below = splitme[row_to_split+1:]
            line_to_split = splitme[row_to_split]
            left = line_to_split[:col_to_split] 
            right = line_to_split[col_to_split:] 

            if left :
                above.extend([left])
            below = [right] + below

            return (above,below)
            
        # split the recipe from the rule
        first_line_pos = self.virt_lines[0][0]["pos"]
        row_to_split = truncate_pos[VCHAR_ROW] - first_line_pos[VCHAR_ROW]

        above,below = split_2d_array(self.virt_lines, row_to_split, truncate_pos[VCHAR_COL] )
#        print("above=","".join([c["char"] for c in itertools.chain(*above) if not c["hide"]]))
#        print("below=","".join([c["char"] for c in itertools.chain(*below) if not c["hide"]]))

        self.virt_lines = above

        above,below = split_2d_array(self.phys_lines, row_to_split, truncate_pos[VCHAR_COL] )
        print("above=",above)
        print("below=",below)

        # recipe lines are what we found after the rule was parsed
        recipe_lines = below
        self.phys_lines = above

        # stupid human check
        assert recipe_lines[0][0]==';'

        # truncate the iterator (stop the iterator)
        self.virt_iterator.stop()

        return recipe_lines

class RecipeVirtualLine(VirtualLine):
    # This is a block containing recipe(s). Don't collapse around backslashes. 
    def collapse_virtual_line(self):
        pass

def test_line_cont():
    test_list = ( 
        ( "this is a test\n",   False ),
        ( "this is a test\\\n", True ),
        ( "this is a test",     False),

        # Windows, DOS
        ( "this is a test\\\r\n", True ),
        ( "this is a test\\\n\r", True ),

        # short stuff
        ( "", False ),
        ( "\\", False ),
        ( "\\\n", True ),

    )

    for test in test_list : 
        test_string,result = test
        assert is_line_continuation(test_string)==result, (test_string,)

def test_vline():
    test_list = ( 
    # single line
    ( "foo : bar ; baz\n", "foo : bar ; baz\n"),
    ( "backslash=\ \n", "backslash=\ \n"),

    # backslash then blank line then end-of-string
    ( r"""space=\

""", "space= \n" ),

    # backslash joining rule + recipe
    ( r"""foo\
:\
bar\
;\
baz
""", "foo : bar ; baz\n" ),

    # another way to write the previous test
    ( "foo2\\\n:\\\nbar\\\n;\\\nbaz\n", "foo2 : bar ; baz\n" ),

    # from ffmpeg
    ( r"""SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS      \
               HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS            \
               ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS                \
               ALTIVEC-OBJS VIS-OBJS                                     \
               MMX-OBJS YASM-OBJS                                        \
               MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS  \
               OBJS HOSTOBJS TESTOBJS
""", "SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS ALTIVEC-OBJS VIS-OBJS MMX-OBJS YASM-OBJS MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS OBJS HOSTOBJS TESTOBJS\n" ),

    # stupid DOS \r\n 0x0d0a <cr><lf>
#    ( """supid-dos:\\\r\nis\\\r\nstupid\r\n""", () ),

    ( r"""more-fun-in-assign\
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
""", "more-fun-in-assign = the leading and trailing white space should be eliminated including blank lines\n" ),

    # This is a weird one. Why doesn't GNU Make give me two \\ here? I only get
    # one. Disable the test for now. Need to dig into make
#    ( r"""literal-backslash-2 = \\\
#        q
#""", "literal-backslash-2 = \\ q\n" ),
#
    ( "foo : # this comment\\\ncontinues on this line\n", 
      "foo : # this comment continues on this line\n" ),

    # end of the tests list
    )

    for test in test_list : 
        # string, validation
        s,v = test
#        print(s,end="")
#        print("s={0}".format(hexdump.dump(s,16)),end="")

        # VirtualLine needs an array of lines from a file.  The EOLs must be
        # preserved. But I want a nice easy way to make test strings (one
        # single string). 
        #
        # The incoming string will be one single string with embedded \n's
        # (rather than trying to create an array of strings by hand).
        # Split the test string by \n into an array. Then restore \n on each line.
        # The [:-1] skips the empty string after the final \n
        file_lines = s.split("\n")[:-1]
        lines = [ line+"\n" for line in file_lines ]
        
#        print( "split={0}".format(s.split("\n")))
#        print( "lines={0} len={1}".format(lines,len(lines)),end="")

        vline = VirtualLine( lines, 0 )
        for line in vline.virt_lines : 
            print(line)
        print(vline)

        s = str(vline)
        print("s={0}".format(hexdump.dump(s,16)))
        print("v={0}".format(hexdump.dump(v,16)))
        assert s==v

def run_tests() : 
    test_line_cont()
    test_vline()
    # need moar tests!

def main() : 
    run_tests()
    # more?

if __name__=='__main__':
    main()

