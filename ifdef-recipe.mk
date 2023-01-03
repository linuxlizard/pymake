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
    $(info thiz BAZ also not part of the recipe)

	$(info oh look a leading tab!)

