FOO=1
ifndef FOO
$(error missing FOO)
endif

undefine FOO
ifdef FOO
$(error FOO still lives)
endif

@:;@:

