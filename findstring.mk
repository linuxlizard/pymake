$(info $(findstring a,a b c))
$(info $(findstring a, b c))

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
x=a b c d e f g
$(info 1 a=$(findstring a,$x))
$(info 2 a=$(findstring a, $x ))
$(info 3 a=$(findstring a,$x $x $x))  # single a (no duplicates)
$(info 4 a=$(findstring a,$x$x$x))  # single a (no duplicates)

$(info a b=$(findstring a b,$x))  # a b ; whitespace in "find" param is preserved as part of the string
$(info a  b=$(findstring a  b,$x))  # a b ; whitespace in "find" preserved
$(info a  b=$(findstring a  b, a  b  c  d  e  f  g ))  # a  b

$(info blank=>>$(findstring a b q,$x)<<)  # >><<  (blank)

$(info 1 the=$(findstring the,hello there all you rabbits))  # the (partial string match is valid)
$(info 2 the=$(findstring the,now is the time for all good men to come to the aid of their country))  # the (only single match)

t=t
h=h
e=e
$(info 3 the=$(findstring $t$h$e,now is the time for all good men to come to the aid of their country))  # the (only single match)
$(info 4 the=$(findstring $t$h$e,now is the time for all good men to come to the aid of their country))  # the (only single match)

@:;@:

