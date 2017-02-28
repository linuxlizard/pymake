# davep 20-Mar-2016 ; symbol table

import os
import logging

logger = logging.getLogger("pymake.symtable")

class DuplicateFunction(Exception):
	pass

class SymbolTable(object):
	def __init__(self):
		self.symbols = {}

	def add(self, name, value):
		logger.debug("%s store \"%s\"=\"%s\"", self, name, value)

		# an attempt to store empty string is a bug
		assert len(name)

		self.symbols[name] = value

	def fetch(self, s):
		# now try a var lookup 
		# Will always return an empty string on any sort of failure. 
		logger.debug("fetch sym=\"%s\"", s)
		if not len(s):
			return ""
		try:
			return self.symbols[s]
		except KeyError:
			logger.debug("sym=%s not in symbol table", s)
			# try environment
			value = os.getenv(s)
			if value is None:
				return ""
			logger.debug("sym=%s found in environ", s)
			return value

