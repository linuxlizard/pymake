# from the GNU Make manual
# (slightly modified to use /dev/null for second filename)

name1 := $(lastword $(MAKEFILE_LIST))
include /dev/null
name2 := $(lastword $(MAKEFILE_LIST))

$(info origin=$(origin MAKEFILE_LIST))
$(info MAKEFILE_LIST=$(MAKEFILE_LIST))

all:
	@echo name1 = $(name1)
	@echo name2 = $(name2)

