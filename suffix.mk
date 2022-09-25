$(info c=$(suffix src/foo.c src-1.0/bar.c hacks .c))

$(info dot=$(suffix .ssh))
$(info dot=$(suffix ......foo.....c))
$(info dot=$(suffix ......foo.....c...c.c))
$(info dot=$(suffix ..))

$(info long=$(suffix .thisisalongnamethatviolatescommonsense))

# weird, this evaluates to empty ; why?
$(info weird=$(suffix foo.c/bar))

$(info path=$(suffix /this/is/a/test/foo.c))

$(info mydir=$(suffix $(sort $(wildcard *.py *.mk))))

$(info empty=>>$(suffix foo bar baz qux)<<)

@:;@:

