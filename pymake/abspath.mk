
$(info $(abspath abspath.mk))

a=abspath.mk
$(info $(abspath $a))
$(info $(abspath $a $a))

$(info $(abspath $(wordlist 1,3,$(sort $(wildcard *.py)))))

@:;@:

