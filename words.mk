$(info $(words foo bar baz))
$(info $(words      foo       bar 				baz			))
$(info $(words $(shell ls *.mk)))

foo=
$(info $(words $(foo)))

$(info $(words ))

# "Returns the number of words in text. Thus, the last word of text is:"
# -- gnu make manual
text := $(shell ls *.py)
$(info $(word $(words $(text)),$(text)))

@:;@:

