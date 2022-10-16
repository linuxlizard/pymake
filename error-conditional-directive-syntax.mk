# parsed as a conditional directive but looks like a rule
# *** invalid syntax in conditional.
ifdef : ; @echo I am here $@

# Note if split across multiple lines, is still a conditional.
# Treated as conditional directives but looks like a rule.
ifdef : 
	@echo I am here $@
endif

@:;@:


