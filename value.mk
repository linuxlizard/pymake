# from the gnu make manual
FOO = $PATH
A=1

#FOO,FOO=both the foos
#$(info info value FOO,FOO=>>$(value FOO,FOO)<<)
#FOO,FOO1=both the foos
#$(info info value FOO,FOO-A=>>$(value FOO,FOO$A)<<)

#$(info info FOO=>>$(FOO)<<)
$(info info value FOO=>>$(value FOO)<<)
$(info info value FOO=>>$(value FOO)<<)
$(info info value FOO,FOO=>>$(value FOO,FOO)<<)

BAR:=FOO
$(info info value BAR=>>$(value $(BAR))<<)

all:
	@echo $(FOO)
	@echo $(value FOO)
