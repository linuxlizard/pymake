test=$(file < firstword.mk)
#$(info test=$(test))

dollar=$$
$(info dollar=$(dollar))

openparen=(

# convert $(firstword) tests to $(lastword) tests
$(file > out.mk, $(subst $(dollar)$(openparen)firstword,$(dollar)$(openparen)lastword,$(test)))

@:;@:
