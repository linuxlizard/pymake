#!/usr/bin/env python3

__all__ = [ "ParseError",
			"NestedTooDeep",
			"TODO",
		  ]

# test/debug flags
# assert() in ParseError() constructor TODO make this a command line arg
assert_on_parse_error = False  

class ParseError(Exception):
	filename = None   # filename containing the error
	pos = (-1,-1)  # row/col of positin, zero based
	code = None	  # code line that caused the error (a VirtualLine)
	description = "(No description!)" # useful description of the error

	def __init__(self,*args,**kwargs):
		if assert_on_parse_error : 
			# handy for stopping immediately to diagnose a parse error
			# (especially when the parse error is unexpected or wrong)
			assert 0

		super().__init__(*args)
		self.vline = kwargs.get("vline",None)
		self.pos = kwargs.get("pos",None)
		self.filename = kwargs.get("filename",None)
		self.description = kwargs.get("description",None)

	def __str__(self):
		return "parse error: filename=\"{0}\" pos={1} src=\"{2}\": {3}".format(
				self.filename,self.pos,str(self.vline).strip(),self.description)

class NestedTooDeep(Exception):
	pass

class TODO(Exception):
	pass


