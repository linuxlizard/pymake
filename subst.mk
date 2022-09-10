# davep 20170225 ; subst first real function to be implemented

$(info $(subst ee,EE,feet on the street))
$(info $(subst ee,EE,feet   on    the    street  <<))

feet:=feet
street:=street
$(info $(subst ee,EE,$(feet) on the $(street)))

# make seems to ignore whitespace between "subst" and first arg
path:=$(subst           :, dave ,$(PATH))
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

alphabet=abcdefghijklmnopqrstuvwxyz
$(info alphabet=$(alphabet))
# for LOLs
UPPERCASE=$(subst z,Z,$(subst y,Y,$(subst x,X,$(subst w,W,$(subst v,V,$(subst u,U,$(subst t,T,$(subst s,S,$(subst r,R,$(subst q,Q,$(subst p,P,$(subst o,O,$(subst n,N,$(subst m,M,$(subst l,L,$(subst k,K,$(subst j,J,$(subst i,I,$(subst h,H,$(subst g,G,$(subst f,F,$(subst e,E,$(subst d,D,$(subst c,C,$(subst b,B,$(subst a,A,$(target)))))))))))))))))))))))))))

target:=$(alphabet)
$(info ALPHABET=$(UPPERCASE))

target:=The quick brown fox jumped over the lazy dogs
$(info UPPERCASE=$(UPPERCASE))

# error cases <=2 commas
#$(info >$(subst )<) # *** insufficient number of arguments (1) to function `subst'.  Stop.  
#$(info >$(subst ,)<) # *** insufficient number of arguments (2) to function `subst'.  Stop.
$(info >$(subst ,,)<) # (thumbsup)

@:;@:
