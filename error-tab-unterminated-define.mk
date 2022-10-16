# Leading <tab> creates confusion.  
# "missing 'enddef', unterminated 'define'  
# Might be a GNU Make bug?  Works fine with <space>endef as opposed to this <tab>endef
	define foo
		echo foo
	endef

define bar
endef

@:;@:

