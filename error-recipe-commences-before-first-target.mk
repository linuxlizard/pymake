# not treated as a rule (ignored)
	# foo bar baz

# valid
	FOO:=BAR

# treated as a rule
# "recipe commences before first target"
	$(info FOO=$(FOO))

@:;@:


