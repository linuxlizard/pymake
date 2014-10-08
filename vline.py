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
                          "pos"  : (row_idx+self.starting_file_line,col_idx),
                          "hide" : False } 
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
        # the tokenizer.
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
        row_to_split = truncate_pos[ROW] - first_line_pos[ROW]

        above,below = split_2d_array(self.virt_lines, row_to_split, truncate_pos[COL] )
#        print("above=","".join([c["char"] for c in itertools.chain(*above) if not c["hide"]]))
#        print("below=","".join([c["char"] for c in itertools.chain(*below) if not c["hide"]]))

        self.virt_lines = above

        above,below = split_2d_array(self.phys_lines, row_to_split, truncate_pos[COL] )
        print("above=",above)
        print("below=",below)

        # recipe lines are what we found after the rule was parsed
        recipe_lines = below
        self.phys_lines = above

        # stupid human check
        assert recipe_lines[0][0]==';'

#        # split the recipe from the rule
#        first_line_pos = self.virt_lines[0][0]["pos"]
#        phys_row_to_split = truncate_pos[ROW] - first_line_pos[ROW]
#        above = self.phys_lines[:phys_row_to_split]
#        below = self.phys_lines[phys_row_to_split+1:]
#        line_to_split = self.phys_lines[phys_row_to_split]
#        left = line_to_split[:truncate_pos[COL]] 
#        right = line_to_split[truncate_pos[COL]:] 
#
#        if left :
#            above.extend([left])
#        below = [right] + below
#        print("above=",above)
#        print("below=",below)

        # truncate my virtual line 
        # TODO

        # truncate the iterator (stop the iterator)
        self.virt_iterator.stop()

        return recipe_lines


class RecipeVirtualLine(VirtualLine):
    # This is a block containing recipe(s). Don't collapse around backslashes. 
    def collapse_virtual_line(self):
        pass

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

def parse_recipes( file_lines, semicolon_vline=None ) : 
    # I put stuff like this in here because I lose track of what I'm doing
#    assert type(file_lines)==type([]),type(file_lines)
#    assert type(file_lines[0])==type(""),type(file_lines[0])
#    assert type(semicolon_str)==type(""),type(semicolon_str)

    print("parse_recipes()")
    print( file_lines.remain() )

    state_start = 1
    state_comment_backslash = 2
    state_recipe_backslash = 3

    state = state_start

    # array of Recipe
    recipe_list = []

    # array of text lines (recipes with \)
    lines_list = []

    if semicolon_vline : 
        # we have something that trails a ; on the rule
        recipe = tokenize_recipe(iter(semicolon_vline))
        print("recipe={0}".format(recipe.makefile()))
        recipe.set_code( semicolon_vline )
        recipe_list.append(recipe)

    for line in file_lines : 
#        print("")
        print( "l state={0}".format(state))
        print( hexdump.dump(line,16), end="" )

        if state==state_start : 
            if line.startswith(recipe_prefix):
                # TODO handle DOS line ending
                if line.endswith('\\\n'):
                    lines_list = [ line ] 
                    state = state_recipe_backslash
                else :
                    # single line
                    recipe_vline = RecipeVirtualLine([line],file_lines.idx)
                    recipe = tokenize_recipe(iter(recipe_vline))
#                    recipe = tokenize_recipe(ScannerIterator(line))
                    print("recipe={0}".format(recipe.makefile()))
                    recipe.set_code(recipe_vline)
                    recipe_list.append(recipe)
            else : 
                line_stripped = line.strip()
                if len(line_stripped)==0:
                    # ignore blank lines
                    pass
                elif line_stripped.startswith("#"):
                    # ignore makefile comments
                    # TODO handle DOS line ending
                    print("recipe comment",line_stripped)
                    if line.endswith('\\\n'):
                        lines_list = [ line ] 
                        state = state_comment_backslash
                else:
                    # found a line that doesn't belong to the recipe;
                    # done with recipe list
                    file_lines.pushback()
                    break

        elif state==state_comment_backslash : 
            # TODO handle DOS line ending
            lines_list.append( line )
            if not line.endswith('\\\n'):
                # end of the makefile comment (is ignored)
                state = state_start

        elif state==state_recipe_backslash : 
            # TODO handle DOS line ending
            lines_list.append( line )
            if not line.endswith('\\\n'):
                # now have an array of lines that need to be one line for the
                # recipes tokenizer
                recipe_vline = RecipeVirtualLine(lines_list,file_lines.idx)
                recipe = tokenize_recipe(iter(recipe_vline))
                recipe.set_code(recipe_vline)
                recipe_list.append(recipe)

                # go back and look for more
                state = state_start

        else : 
            # wtf?
            assert 0,state

    print("bottom of parse_recipes()")

    return RecipeList(recipe_list)

def parse_a_line(line_iter,virt_line): 
    # pull apart a single line into token/symbol(s)
    #
    # line_iter - the iterator across the entire file 
    #             (a Rule includes the RecipeList so need to get the entire file)
    # virt_line - the current line we need to tokenize (a VirtualLine)

    assert isinstance(line_iter,ScannerIterator),(type(line_iter),)
    assert isinstance(virt_line,VirtualLine),(type(virt_line),)

    statement_iter = iter(virt_line)
    token = tokenize_statement(statement_iter)

    # If we found a rule, we need to change how we're handling the
    # lines. (Recipes have different whitespace and backslash rules.)
    if isinstance(token,RuleExpression) : 
        # rule line can contain a recipe following a ; 
        # for example:
        # foo : bar ; @echo baz
        #
        # The rule parser should stop at the semicolon. Will leave the
        # semicolon as the first char of iterator
        # 
        print("rule={0}".format(str(token)))

        # truncate the virtual line that precedes the recipe (cut off
        # at a ";" that might be lurking)
        #
        # foo : bar ; @echo baz
        #          ^--- truncate here
        #
        # I have to parse the full like as a rule to know where the
        # rule ends and the recipe(s) begin. The backslash makes me
        # crazy.
        #
        # foo : bar ; @echo baz\
        # I am more recipe hur hur hur
        #
        # The recipe is "@echo baz\\\nI am more recipe hur hur hur\n"
        # and that's what needs to exec'd.
        remaining_vchars = statement_iter.remain()
        if len(remaining_vchars)>0:
            # truncate at position of first char of whatever is
            # leftover from the rule
            truncate_pos = remaining_vchars[0]["pos"]
#            print("truncate_pos={0}".format(truncate_pos))

            recipe_str_list = virt_line.truncate(truncate_pos)


#            # split the recipe from the rule
#            first_line_pos = virt_line.virt_lines[0][0]["pos"]
#            phys_row_to_split = truncate_pos[ROW] - first_line_pos[ROW]
#            above = virt_line.phys_lines[:phys_row_to_split]
#            below = virt_line.phys_lines[phys_row_to_split+1:]
#            line_to_split = virt_line.phys_lines[phys_row_to_split]
#            left = line_to_split[:truncate_pos[COL]] 
#            right = line_to_split[truncate_pos[COL]:] 
#
#            if left :
#                above.extend([left])
#            recipe = [right] + below
#            print("rule=",above)
#            print("recipe=",recipe)

            # make a new virtual line from the semicolon trailing
            # recipe (using a virtual line because backslashes)
            dangling_recipe = RecipeVirtualLine(recipe_str_list,truncate_pos[ROW])
            print("dangling={0}".format(dangling_recipe))
            print("dangling={0}".format(dangling_recipe.virt_lines))
            print("dangling={0}".format(dangling_recipe.phys_lines))

            recipe_list = parse_recipes( line_iter, dangling_recipe )
        else :
            recipe_list = parse_recipes( line_iter )

        assert isinstance(recipe_list,RecipeList)

        print("recipe_list={0}".format(str(recipe_list)))

        # attach the recipe(s) to the rule
        token.add_recipe_list(recipe_list)

    token.set_code(virt_line)

    return token

def parse_lines(file_lines): 
    # File_lines is an array of strings.
    # Each string should be terminated by an EOL.
    # Handle cases where line is continued after the EOL by a \+EOL
    # (backslash).

    # I put stuff like this in here because I lose track of what I'm doing
    assert type(file_lines)==type([])
    assert type(file_lines[0])==type("")

    state_start = 1
    state_backslash = 2
    state_tokenize = 3
    
    state = state_start 

    # array of Symbols we have parsed in the file
    code_block_list = []

    # we need an iterator across our lines that supports pushback
    line_iter = ScannerIterator(file_lines)

    # can't use enumerate() because the line_iter will also be used inside
    # parse_recipes(). 
    for line in line_iter :
        # line_iter.idx is the *next* line number counting from zero 
        line_number = line_iter.idx-1
        print("line_num={0} state={1}".format(line_number,state))
        print("{0}".format(hexdump.dump(line),end=""))

        if state==state_start : 
            start_line_stripped = line.strip()

            # ignore blank lines
            if len(start_line_stripped)==0:
                continue

            line_list = [ line ] 

            starting_line_number = line_number
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

        if state==state_tokenize: 
            # is this a line comment?
            if start_line_stripped.startswith("#") :
                # ignore
                state = state_start
                continue

            # make a virtual line (joins together backslashed lines into one
            # line visible through an iterator)
            virt_line = VirtualLine(line_list,starting_line_number)
            del line_list # detach the ref (VirtualLine keeps the array)

            # now take apart the line into symbol/tokens
            token = parse_a_line(line_iter,virt_line)

            # save the parsed symbol with its code 
            code_block_list.append( token ) 

            # back around the horn
            state = state_start

    return code_block_list 

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

        # This seems silly but VirtualLine needs an array of lines from a file.
        # The EOLs must be preserved. But I want a nice easy way to make
        # test strings. So split the test string by \n but then restore \n on
        # each line.
        # The [:-1] skips the empty string after the final \n
        file_lines = s.split("\n")[:-1]
        lines = [ line+"\n" for line in file_lines ]
        
#        print( "split={0}".format(s.split("\n")))
#        print( "lines={0} len={1}".format(lines,len(lines)),end="")

        vline = VirtualLine( lines )
        for line in vline.virt_lines : 
            print(line)
        print(vline)

        s = str(vline)
        print("s={0}".format(hexdump.dump(s,16)))
        print("v={0}".format(hexdump.dump(v,16)))
        assert s==v

def main() : 
    if len(sys.argv) < 2 : 
        run_tests()
        return

    infilename = sys.argv[1]

    with open(infilename,'r') as infile :
        file_lines = infile.readlines()

    block_list = parse_lines(file_lines)
    for block in block_list : 
        assert isinstance(block,Symbol),(type(block),)
        assert hasattr(block,"code")
        print("{0}".format(block.code),end="")
        if isinstance(block,RuleExpression):
            for recipe in block.recipe_list : 
                print("{0}".format(recipe.code))

    print("makefile=",",\\\n".join( [ "{0}".format(block) for block in block_list ] ) )


if __name__=='__main__':
    main()

