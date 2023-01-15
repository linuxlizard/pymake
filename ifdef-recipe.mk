# A recipe containing an ifdef block.
#

foo:
	@echo foo?
ifdef FOO
	@echo hello from foo!
endif # FOO
	@echo bar
ifdef FOO
$(info this FOO is not part of the recipe)
endif

bar:
	@echo bar?
ifdef BAR
    @echo this is still part of the recipe; is an error but only if BAR defined
endif
	@echo bar

baz:
	@echo baz?
ifdef BAZ
    $(info this BAZ is not part of the recipe)
endif
    $(info this BAZ also not part of the recipe)

	$(info oh look a leading tab!)

#	$(info leading tab before any rules) # this fails

# endef cannot have leading tab
	define DAVE
	42
endef 

	# directives allowed with leading tab
	# export unexport vpath include -include sinclude load 
	# and conditionals
	# (others?)
	export DAVE

	# variable assignment allowed w/ leading tab
	a := a

:
	@echo no targets

foo:
	@echo foo?
ifdef FOO
	@echo hello from foo!
endif # FOO
	@echo bar

ifdef BAR
    $(info this is end of the rule when BAR is defined)
endif

	$(info foo bar baz)echo foo bar baz
	echo foo

	@# captured as a recipe ("ifdef: No such file or directory")
#	ifdef BAZ
#		baz baz
#	endif

	b := b

