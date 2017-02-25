#!/usr/bin/env python3

# Validate output of test makefiles & my parser
# davep 11-Sep-2014
#
# The output should be:  token space LHS token RHS
#
# The first character is the separator between the expected output and the
# actual output. Usually "=" is used except in cases where the string itself
# might contain "= .
#
# The separator token is followed by a single space (for human readability).
# All spaces after the first space are significant! Don't strip() the strings!


import sys

# require Python 3.x for best Unicode handling
if sys.version_info.major < 3:
	raise Exception("Requires Python 3.x")

def validate(infile):
	while 1 :
		# kill trailing \n
		line = infile.readline()[:-1]
		if len(line)<=0:
			return

		# Make 3.81 automatically prepends "-c" onto recipe lines when
		# launching SHELL 
		# Make >= 3.82 has SHELLOPTS to override 
		if line.startswith("-c "):
			line = line[3:]

		print("line={0}".format(line))
		separator = line[0]
		fields = line[2:].split(separator)
		assert len(fields)==2,(len(fields),(line,fields))

		for z in zip( (fields[0],), (fields[1],) ):
			print( z )
			msg = "\"{0}\"!=\"{1}\"".format(z[0],z[1])
			if z[0]!=z[1] :
				print("fail lhs=^",z[0],"$")
				print("fail rhs=^",z[1],"$")
			assert z[0]==z[1], (line,msg)

def usage():
	print("validate test makefile output",file=sys.stderr)
	print("usage: {0} [file [file...] | -".format(sys.argv[0]), file=sys.stderr )
	print(" - : read from stdin",file=sys.stderr)

def main(): 
	if len(sys.argv)==1:
		usage()
		sys.exit()

	for f in sys.argv[1:]:
		if f =="-" :
			validate(sys.stdin)
		else:
			with open(f) as infile:
				validate(infile)

if __name__=='__main__':
	main()

