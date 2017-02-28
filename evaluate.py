#!/usr/bin/env python3

# davep 12-Mar-2016 ; evaluate the Makefile AST

import sys
import logging

logger = logging.getLogger("pymake.evaluate")

def evaluate(symbol_list, symbol_table):
	s = ""
	for sym in symbol_list:
		logger.debug("sym=%s", sym)
		s += sym.eval(symbol_table)
		logger.debug("eval result s=\"%s\"", s)
		logger.debug("symbol_table=%s", symbol_table)
	return s
