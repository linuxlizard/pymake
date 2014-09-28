# Study various horrible ways comments can be abused
# 
# davep 28-sep-2014


# this is a comment (duh)

all : a-rule # this is a comment
# this comment ignored by make
	# this comment passed to shell

#this is a comment\
with\
backslashes\
and\
should\
be\
ignored

a-rule : a-prereq # a comment
	@echo $@ $^

# comments comments comments
a-prereq : # comment \
comment\
comment\
comment
	@echo $@ $^

this-is-a-variable = # this is a comment
$(info = =$(this-is-a-variable)) 

this-is-also-a-variable = # this is a comment\
that\
runs\
along\
multiple\
lines
$(info = =$(this-is-also-a-variable))  # empty output

-include foo.mk # how about comments here?

