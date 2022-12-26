# test the += operator

# simply expanded
FOO:=bar
FOO+=baz
$(info FOO=$(FOO))

# recursively expanded
FOO=abc
FOO+=xyz
$(info FOO=$(FOO))

# recursively expanded
BAR=$(FOO)
BAR+=bar
$(info BAR=$(BAR))

# now replace FOO; BAR should change
FOO=pqr
$(info BAR=$(BAR))

# append to doesn't exist
BAZ+=baz
$(info BAZ=$(BAZ))

PHRASE=feet on the street
FOO=$(subst ee,EE,$(PHRASE))

FOO+=bar
$(info FOO=$(FOO))

PHRASE=meet me in St Louis
$(info FOO=$(FOO))

undefine FOO
undefine BAR
undefine PHRASE

PHRASE=feet on the street
FOO=$(subst ee,EE,$(PHRASE))
BAR=bar

# multiple recursive variables (append recursive to recursive)
FOO+=$(BAR)
$(info FOO=$(FOO))
PHRASE=sleepwalking through engineering
$(info FOO=$(FOO))
BAR=baz
$(info FOO=$(FOO))



@:;@:

