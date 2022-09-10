$(info $(words foo bar baz))
$(info $(words      foo       bar 				baz			))
$(info $(words $(shell ls *.mk)))

foo=
$(info $(words $(foo)))

$(info $(words ))

#$(info $(word 0, foo bar baz, 0))  # *** first argument to 'word' function must be greater than 0.  Stop.
$(info $(word 1, foo bar baz))
$(info $(word 2, foo bar baz))
$(info $(word 3, foo bar baz))
$(info $(word 4, foo bar baz))

$(info $(word       1, foo bar baz))
$(info $(word				1, foo bar baz))

$(info $(firstword foo bar baz))
$(info $(lastword foo bar baz))

s=foo bar baz
$(info $(findstring foo, $s))
$(info $(findstring foo, a b c $s d e f g))

$(info $(findstring foo, foo bar baz))
$(info $(findstring qux, foo bar baz))

s:=foo bar baz
$(info $(findstring foo, $s))
$(info $(findstring foo, a b c $s d e f g))

s=foo bar baz
$(info $(findstring foo, $s))
$(info $(findstring foo, a b c $s d e f g))

@:;@:

