# treated as a recipe
# "recipe commences before first target"
	ifdef CC
		$(info CC=$(CC))
	else
		$(error CC is not set)
	endif

@:;@:

