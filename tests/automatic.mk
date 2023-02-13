# test automatic variables
# TODO many more tests

.PHONY: all foo bar baz quz
all: foo ; @echo all running rule $@

foo: bar baz qux ; @echo running rule $@
	@echo foo prereq list $^
	@echo foo first prereq $<

# $^ eliminates duplicates
# $+ reports all prereqs in order
bar: baz qux baz baz
	@echo bar prereq list no dups $^
	@echo bar prereq list w/ dups $+

baz: ; @echo running rule $@

qux: ; @echo running rule $@


