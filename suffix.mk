$(info $(suffix src/foo.c src-1.0/bar.c hacks))

$(info dot=$(suffix .ssh))
$(info dot=$(suffix ......foo.....c))
$(info dot=$(suffix ......foo.....c...c.c))
$(info dot=$(suffix ..))

$(info long=$(suffix .thisisalongnamethatviolatescommonsense))

# weird, this evaluates to empty ; why?
$(info weird=$(suffix foo.c/bar))

@:;@:

