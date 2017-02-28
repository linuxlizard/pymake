# davep 20170225 ; subst first real function to be implemented

$(info $(subst ee,EE,feet on the street))

# make seems to ignore whitespace between "subst" and first arg
path:=$(subst           bin,dave ,$(PATH))
$(info $(path))

#$(error stop)

path:=$(subst :, ,$(PATH))
$(info $(path))

q=q
path:=$(subst		:, $q ,$(PATH))
$(info $(path))

space= 
path:=$(subst :,$(space),$(PATH))
$(info $(path))


path:=$(PATH)
split_path=$(subst :, ,$(path))
path=foo:bar:baz:
$(info $(split_path))

# need a literal comma must use a intermediate var
comma=,
s:=The,Quick,Brown,Fox,Jumped,Over,The,Lazy,Dogs
$(info $(subst $(comma), ,$s))

$(info $(subst $(comma),$q,$s))

# error cases <=2 commas
#$(info >$(subst )<) # *** insufficient number of arguments (1) to function `subst'.  Stop.  
#$(info >$(subst ,)<) # *** insufficient number of arguments (2) to function `subst'.  Stop.
$(info >$(subst ,,)<) # (thumbsup)

@:;@:
