#!/usr/bin/env python3

# test vline_iter and line_iter stay in sync

import sys
from pymake import get_vline
from scanner import ScannerIterator
import random

def iter_test(file_lines):
	line_iter = ScannerIterator(file_lines)
	vline_iter = get_vline(line_iter)

	while 1: 
		if random.choice((0,1)):
			s = next(line_iter)
		else : 
			s = next(vline_iter)
		yield s

def iter_test_filename(infilename):
	with open(infilename,'r') as infile :
		# tortuous filter to kill comment lines and empty lines or the test
		# will fail because vline eats those
		file_lines =  [ l for l in infile.readlines() if 
							not l.lstrip().startswith("#") and
							len(l.strip()) > 0 ]

#	print(file_lines)
	file_lines_out = list(iter_test(file_lines))
#	print([str(s) for s in file_lines_out])

	for l,r in zip(file_lines,file_lines_out):
		assert l==str(r),(l,str(r))

def iter_test_range():
	nums = [ str(n) for n in range(100) ]
	nums_out = list(iter_test(nums))

	for l,r in zip(nums,nums_out):
		assert l==str(r),(l,str(r))

if __name__=='__main__':
	iter_test_range()

	infilename = sys.argv[1]
	iter_test_filename(infilename)

