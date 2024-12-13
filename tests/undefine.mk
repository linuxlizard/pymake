FOO=1
ifndef FOO
$(error missing FOO)
endif

# will undefine a variable named 'FOO:=3'
undefine FOO:=3
ifndef FOO
$(error missing FOO)
endif
$(info FOO=$(FOO))

undefine FOO
ifdef FOO
$(error FOO still lives)
endif

FOO:=1
BAR:=2
BAZ:=3
ifndef FOO
$(error missing FOO)
endif
ifndef BAR
$(error missing BAR)
endif
ifndef BAZ
$(error missing BAZ)
endif

# will undefine a variable named "FOO BAR BAZ"
undefine FOO BAR BAZ
ifndef FOO
$(error FOO wrongly undefined)
endif
ifndef BAR
$(error BAR wrongly undefined)
endif
ifndef BAZ
$(error BAZ wrongly undefined)
endif

undefine FOO
undefine BAR
undefine BAZ
ifdef FOO
$(error FOO)
endif
ifdef BAR
$(error BAR)
endif
ifdef BAZ
$(error BAZ)
endif

# remove a built-in
$(info .VARIABLES is from $(origin .VARIABLES))
undefine .VARIABLES
$(info .VARIABLES=>>$(.VARIABLES)<< now from $(origin .VARIABLES))
ifdef .VARIABLES
$(error .VARIABLES still lives)
endif

@:;@:

