# Experiment with target specific rules.
# GNU Make manual 6.11
# davep 19-Sep-2014

CC=gcc
LD=ld

all : specific normal

normal : 
	@echo $@ CC=$(CC) LD=$(LD)

specific : CC=mycc
specific : LD=myld
specific : other
	@echo $@ CC=$(CC) LD=$(LD)

other : CC=$(shell which gcc)
other : multiple
	@echo $@ CC=$(CC) LD=$(LD)

# multiple assignments 
multiple: CC=intel-cc LD=intel-ld
multiple: spaces
	@echo $@ CC=$(CC) LD=$(LD)

this is a test=CC
spaces: $(this is a test)=this is a test
spaces:
	@echo $@ CC=$(CC) LD=$(LD) $(this is a test)

# Anything after the assignment operator is treated as one token. The CC below creates one big string.
FOO=BAR
rules: CC=potato-cc LD=potato-ld spaces CROSS_COMPILE=potato $(FOO) potato
rules:
	@echo $@ CC=@@$(CC)@@ LD=@@$(LD)@@ CROSS_COMPILE=$(CROSS_COMPILE) TEST=$(this is a test)

# GNU Make only preserves one trailing space.
# Leading spaces are discarded.
# Comment is successfully ignored.
more-spaces :   CC   =   single-trailing-space-cc 
more-spaces :   LD    =     lots-of-trailing-spaces-ld      # I am a comment
more-spaces:
	@echo $@ CC=@@$(CC)@@ LD=@@$(LD)@@ TEST=$(this is a test)

