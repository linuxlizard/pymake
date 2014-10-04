#!/usr/bin/env python3

# "Virtual Block" -- a 2D array of characters with visible/not visible
# attribute. 
#
# Created to handle joining backslash'd lines together for the tokenizer. Has
# evolved into something that will be useful for the makeifile View. 
#
# davep 01-Oct-2014

import sys
import itertools

import hexdump
from sm import *

eol = set("\r\n")
whitespace = set( ' \t' )

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

# indices into VirtualLine's characters' position.
ROW = 0
COL = 1

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
        # Create a 2-d array from our 2-d array.
        # The new 2-d array will be the characters with their row,col in the
        # 2-d array. 

        self.virt_lines = []
        for row_idx,line in enumerate(self.phys_lines) : 
            vline = []
            for col_idx,char in enumerate(line):
                # char is the original character
                # pos is the (row,col) of the char in the file
                # hide indicates a hidden character (don't feed to the
                # tokenizer, don't highlight in View)
                vchar = { "char" : char, 
                          "pos"  : (row_idx,col_idx),
                          "hide" : False } 
                vline.append(vchar)
            self.virt_lines.append(vline)

#            print("virt_lines={0}".format(self.virt_lines))

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
        # A list of the characters that are still valid.
        # Make the iterator we will feed to the tokenizer.
        return ScannerIterator( [ c["char"] for c in itertools.chain(*self.virt_lines) if not c["hide"] ] )

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

def run_tests() : 
    test_line_cont()
    test_vline()

def make_line_blocks(file_lines_list): 
    # File_lines is an array of strings.
    # Each string should be terminated by an EOL.
    # Create a VirtualLine object for each line. Handle cases where line is
    # continued after the EOL by a \+EOL (backslash).

    state_start = 1
    state_backslash = 2
    state_recipe = 3
    state_tokenize = 4
    
    state = state_start 
    start_row_idx = 0

    block_list = []

    # we need an iterator that supports pushback
    file_lines = ScannerIterator(file_lines_list)

    for line in file_lines:
        if state==state_start : 
            start_line_stripped = line.strip()

            # ignore blank lines
            if len(start_line_stripped)==0:
                continue

            line_list = [ line ] 
            start_row_idx = file_lines.idx

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

        elif state==state_recipe :
            # we are gathering a list of recipes

            if line.startswith(recipe_prefix):
                line_list.append(line)
            else : 
                print(line_list)
                assert 0

                # End of recipe. Put the line back for someone else to use.
                file_lines.push_back()

                state = state_start

        else:
            # wtf?
            assert 0, state

        if state==state_tokenize: 
            # is this a line comment?
            if start_line_stripped.startswith("#") :
                # ignore
                state = state_start
                continue

            # make a virtual line
            virt_line = VirtualLine(line_list,start_row_idx)
            line_list = None
            line_list = []

            # now tokenize
            my_iter = iter(virt_line)
            token = tokenize_statement(my_iter)

            # if we found a rule, we need to change how we're handling the
            # lines
            if isinstance(token,RuleExpression) : 
                assert len(my_iter.remain())==0
                state = state_recipe
            else : 
                state = state_start
            
            block_list.append( virt_line ) 
            virt_line = None

    return block_list 

def main() : 
    if len(sys.argv) < 2 : 
        run_tests()
        return

    infilename = sys.argv[1]

    with open(infilename,'r') as infile :
        file_lines = infile.readlines()

    block_list = make_line_blocks(file_lines)
    for block in block_list : 
        print("^^{0}$$".format(block),end="")
        

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
        print("s={0}".format(hexdump.dump(s,16)),end="")

        # This seems silly but VirtualLine needs an array of lines from a file.
        # The EOLs must be preserved. But I want a nice easy way to make
        # test strings. So split the test string by \n but then restore \n on
        # each line.
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

if __name__=='__main__':
    main()

