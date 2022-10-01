# Run this test makefile with:  
# make FOO=1 -e -f origin.mk
# (I think)

# undefined
$(info undfined=$(origin undefined))

# environment
$(info PATH=$(origin PATH))

# environment
$(info TERM=$(origin TERM))

# override
override TERM:=vt52
$(info TERM=$(origin TERM))

# file
a:=1
$(info a=$(origin a))

# default
$(info .VARIABLES=$(origin .VARIABLES))
$(info CC=$(origin CC))

$(info FOO=$(FOO) $(origin  FOO))
FOO:=bar
$(info FOO=$(FOO) $(origin  FOO))  # value should not change
override FOO:=bar
$(info FOO=$(FOO) $(origin  FOO))  # "bar override"

# clear a variable
$(info OLDPWD=$(OLDPWD) $(origin OLDPWD))
override OLDPWD=
$(info OLDPWD=$(OLDPWD) $(origin OLDPWD))

# $@ does not exist outside a rule
$(info @=$(origin @))

# TODO these need tests
# errors " *** missing separator. Stop."
#override
#override qq
#override =42
#override 1+2

all:
	@echo in rule origin @= $(origin @)

