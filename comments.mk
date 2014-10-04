# Study various horrible ways comments can be abused
# 
# davep 28-sep-2014


# this is a comment (duh)

all : a-rule comment-in-recipe semicolon-then-comment # this is a comment
# this comment ignored by make
	# this comment passed to shell
	@echo $@

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

comment-in-recipe : 
	@echo $@
# this is a Makefile commment
	@echo after makefile comment # this is a shell comment
	@echo this line is also passed to the shell \
including the continuation \
# and this comment
# this\
 is\
 a\
 makefile\
 comment
	@echo after the big long comment
    # this is also a makefile comment
	@echo after another makefile comment
 end-of-recipe = 42  # end of recipe
$(info = 42=$(end of recipe))

semicolon-then-comment : ; # semicolon comment should be passed to the shell

