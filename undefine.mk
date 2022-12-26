FOO=1
ifndef FOO
$(error missing FOO)
endif

undefine FOO
ifdef FOO
$(error FOO still lives)
endif

# remove a built-in
$(info .VARIABLES is from $(origin .VARIABLES))
undefine .VARIABLES
$(info .VARIABLES=>>$(.VARIABLES)<< now from $(origin .VARIABLES))
ifdef .VARIABLES
$(error .VARIABLES still lives)
endif

@:;@:

