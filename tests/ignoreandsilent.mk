# GNU Make sez a recipe with leading '-' means ignore the error.
# A recipe with a leading '@' doesn't echo the command
# 
all:
	-exit 1
	-@exit 1
	@-exit 1
	@@echo foo
	@@-echo bar
	@echo baz
	---exit 1
	@@echo foo

