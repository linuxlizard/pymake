# this unbalanced parenthesis valid; treated as a string char
path:=$(subst :, ,$(PATH)))
$(info $(path))

//# missing closing )
# error24.mk:6: *** unterminated call to function `subst': missing `)'.  Stop.
path:=$(subst :, ,$(PATH)

@:;@:
