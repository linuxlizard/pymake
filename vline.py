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

import hexdump
from scanner import ScannerIterator
from printable import printable_char, printable_string

eol = set("\r\n")
# can't use string.whitespace because want to preserve line endings
whitespace = set(' \t')

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
	return pos >= 0 and line[pos] == '\\'


# using a class for the virtual char so can interchange string with VirtualLine
# in ScannerIterator
class VChar(object):
	def __init__(self, char, pos, filename):
		self.char = char
		# VCHAR_ROW, VCHAR_COL index into pos
		self.pos = pos

		# show/hide this char (e.g., hide if in a comment or backslash with
		# weird whitespace)
		self.hide = False

		self.filename = filename

	@property
	def linenumber(self):
		return self.pos[VCHAR_ROW]+1

	def __str__(self):
		return self.char


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

	def rstrip(self):
		# 
		# !! WARNING !! Modifies the "string" in-place! Regular strings return a copy.
		# 
		while len(self.chars) and self.chars[-1].char in whitespace:
			self.chars.pop()
		return self

	@classmethod
	def from_string(cls, python_string):
		# make a VCharString from a regular python string (mostly used with
		# testing) the positions and filename will be nonsense)
		return cls([VChar(c, (0,0), "/dev/null") for c in python_string])

class VirtualLine(object):
	def __init__(self, phys_lines_list, starts_at_file_line=-1, filename="/dev/null"):
		logger.debug("VirtualLine line_num=%d filename=%s", starts_at_file_line, filename)
		logger.debug("lines=%s", phys_lines_list)
		# need an array of strings (2-D array of characters)
		assert isinstance(phys_lines_list, list)
		for p in phys_lines_list:
			assert isinstance(p, str), type(p)
		# catch problem code
		try:
			assert len(filename), (type(filename), filename)
		except:
			print(type(filename), filename)
			raise
		# check for integer
		assert starts_at_file_line+1 >= 0, starts_at_file_line

		# where do I come from?
		self.filename = filename

		# save a pristine copy of the original list
		self.phys_lines = phys_lines_list

		# this is where this line blob started in the original source file
		self.starting_file_line = starts_at_file_line

		# create a single array of all the characters with their position in
		# the 2-d array
		self.virt_lines = []
		self._make_virtual_line()

		# Based on the \ line continuation rules, collapse 2-D array into a new
		# 1-D "virtual" array of characters that will be sent to the tokenizer.
		self._collapse_virtual_line()

	def _make_virtual_line(self):
		# Create a 2-D array of VChar from our 2-D array (array of strings).
		#
		# The new 2-D array will be the characters with their row, col in the
		# 2-D array.
		for row_idx, line in enumerate(self.phys_lines):
			vline = []
			for col_idx, char in enumerate(line):
				# char is the original character
				# pos is the (row, col) of the char in the file
				# hide indicates a hidden character (don't feed to the
				# tokenizer, don't highlight in View)
				vchar = VChar(char, (row_idx+self.starting_file_line, col_idx), self.filename)
				vline.append(vchar)
			self.virt_lines.append(vline)

	def _collapse_virtual_line(self):
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
		#	  is \
		#	   a \
		#		 \
		#	test
		# """
		# becomes "this is a test"
		#
		while row < len(self.virt_lines)-1 :
#			print("row={0} {1}".format(row, hexdump.dump(self.phys_lines[row], 16)), end="")

			# start at eol
			col = len(self.virt_lines[row])-1

			# kill EOL
			assert self.virt_lines[row][col].char in eol, (row, col, self.virt_lines[row][col].char)
			self.virt_lines[row][col].hide = True
			col -= 1

			# replace \ with <space>
			assert self.virt_lines[row][col].char=='\\', (row, col, self.virt_lines[row][col].char)
			self.virt_lines[row][col].char = ' '

			# are we now a blank line?
			if self.virt_lines[row][col-1].hide :
				self.virt_lines[row][col].hide = True

			col -= 1

			# eat whitespace backwards
			while col >= 0 and self.virt_lines[row][col].char in whitespace :
				self.virt_lines[row][col].hide = True
				col -= 1

			# eat whitespace forward on next line
			row += 1
			col = 0
			while col < len(self.virt_lines[row]) and self.virt_lines[row][col].char in whitespace :
				self.virt_lines[row][col].hide = True
				col += 1

		# Last char of the last line should be an EOL. There should be no
		# backslash on this last line.
		col = len(self.virt_lines[row])-1
		assert self.virt_lines[row][col].char in eol, (row, col, self.virt_lines[row][col].char)
		col -= 1
		assert self.virt_lines[row][col].char != '\\', (row, col, self.virt_lines[row][col].char)

	def __str__(self):
		# build string from the visible characters
		i = itertools.chain(*self.virt_lines)
		return "".join([c.char for c in i if not c.hide])

	def __iter__(self):
		# This iterator we will feed the characters that are still visible to
		# the tokenizer. Using ScannerIterator so we have pushback. The
		# itertools.chain() joins all the virt_lines together into one
		# contiguous array
		virt_iterator = ScannerIterator([c for c in itertools.chain(*self.virt_lines) if not c.hide])
		return virt_iterator

	def truncate(self, truncate_pos):
		# Created to allow the parser to cut off a block at a token boundary.
		# Need to parse something like:
		# foo : bar ; baz
		# into a rule and a recipe but we won't know where the rule ends and
		# the (maybe) recipes begin until we fully tokenize the rule.
		# foo : bar ; baz
		#		   ^-----truncate here
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

			return (above, below)

		# split the recipe from the rule
		first_line_pos = self.virt_lines[0][0].pos
		row_to_split = truncate_pos[VCHAR_ROW] - first_line_pos[VCHAR_ROW]

		above, below = split_2d_array(self.virt_lines, row_to_split, truncate_pos[VCHAR_COL] )
#		print("above=", "".join([c.char for c in itertools.chain(*above) if not c.hide]))
#		print("below=", "".join([c.char for c in itertools.chain(*below) if not c.hide]))

		self.virt_lines = above

		above, below = split_2d_array(self.phys_lines, row_to_split, truncate_pos[VCHAR_COL] )
#		print("above=", above)
#		print("below=", below)

		# recipe lines are what we found after the rule was parsed
		recipe_lines = below
		self.phys_lines = above

		# stupid human check
		assert recipe_lines[0][0]==';'

		return recipe_lines

	def starting_pos(self):
		# position of this line (in a file) is the position of the first char
		# of the first line
		return self.virt_lines[0][0].pos

	@classmethod
	def from_string(cls, python_string):
		# create a VirtualLine instance from a single string (convenience
		# method for test/debug code)
		return cls([python_string], 0)

	@staticmethod
	def validate(vline_list):
		for v in vline_list : 
			assert isinstance(v, VirtualLine), (type(v), v)

	def get_phys_line(self):
		# rebuild a single physical line (needed when tokenizing recipes)
		return "".join(self.phys_lines)

	def python(self):
		# Return a Python expression representing this virtual line.
		# Used in str() methods from Symbol class hierarchy to round trip the
		# code.
		s = "VirtualLine(["
		s += ", ".join( ["\"{0}\"".format(printable_string(p)) for p in self.phys_lines] )
		s += "], {}, {})".format(self.filename, self.starting_file_line)
		return s

	def get_code(self):
		return { "filename": self.filename,
				 "src" : self.phys_lines,
				 "line": self.starting_file_line}

class RecipeVirtualLine(VirtualLine):
	# This is a block containing recipe(s). Don't collapse around backslashes.
	def _collapse_virtual_line(self):
		pass

def get_vline(filename, line_iter): 
	# GENERATOR
	#
	# line_iter is an iterator that supports pushback
	# that iterates across an array of strings
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
	
	state = state_start 

	# can't use enumerate() because the line_iter will also be used inside
	# parse_recipes() and the idx can change with push_back
	for line in line_iter :
		# line_iter.idx is the *next* line number counting from zero 
		starting_line_number = line_iter.idx-1
		logger.debug("get_vline line_num=%d state=%d", starting_line_number, state)
#		print("{0}".format(hexdump.dump(line), end=""))

		if state==state_start : 
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

		if state==state_tokenize: 
			# is this a line comment?
			if start_line_stripped.startswith("#") :
				# ignore
				state = state_start
				continue

			# make a virtual line (joins together backslashed lines into one
			# line visible through a character by character iterator)
			virt_line = VirtualLine(line_list, starting_line_number, filename)
			del line_list # detach the ref (VirtualLine keeps the array)

			# caller can also use line_iter
			yield virt_line

			# back around the horn
			state = state_start

	return None

