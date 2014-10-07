# Combine target specific variable with 
# Error. "commands commence before first target"
#
# Note: 
#   bar : BAR=FOO ; @echo bar bar bar  
# works. The ; recipe is ignored
#
bar : BAR=FOO 
	@echo bar bar bar

