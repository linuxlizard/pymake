# from the gnu make manual; $PATH is correct vs $(PATH)
FOO = $PATH
P:=Error!

#$(info info FOO=>>$(FOO)<<)
$(info info value FOO=>>$(value FOO)<<)

FOO,FOO=both the foos
$(info info value FOO,FOO=>>$(value FOO,FOO)<<)
A=1
FOO,FOO1=both the foos
$(info info value FOO,FOO-A=>>$(value FOO,FOO$A)<<)
$(info info value FOO,FOO=>>$(value FOO,FOO)<<)

BAR:=FOO
$(info info value BAR=>>$(value BAR)<<)
$(info info value $$BAR=>>$(value $(BAR))<<)

formula=$(foreach foo,$(sort $(wildcard *.py),$(shell wc -l $(foo))))
$(info formula $(value formula))

@:;@:
#all:
#	echo FOO=$(FOO)
#	echo value FOO=$(value (FOO))
