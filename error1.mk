# space after backslash is error
# the following throws error "missing separator"
# The \ isn't treated as a line continuation. The "newline!" is trying to be
# parsed as a statement (assignment|rule|directive)
backslash-space-eol : 
	@echo $@ \ 
newline!


