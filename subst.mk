# davep 20170225 ; subst first real function to be implemented

$(info $(subst ee,EE,feet on the street))
$(info $(subst ee,EE,feet   on    the    street  <<))

$(info b=$(subst a,b,a a a a a a))  # b b b b b b 

feet:=feet
street:=street
$(info $(subst ee,EE,$(feet) on the $(street)))

# make seems to ignore whitespace between "subst" and first arg
path:=$(subst           :, dave ,$(PATH))
$(info p1 $(path))

path:=$(subst :, ,$(PATH))
$(info p2 $(path))

q=q
path:=$(subst		:, $q ,$(PATH))
$(info p3 $(path))

space= 
path:=$(subst :,$(space),$(PATH))
$(info p4 $(path))


path:=$(PATH)
split_path=$(subst :, ,$(path))
path=foo:bar:baz:
$(info p5 $(split_path))

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

# FIXME this fails because my parse_args doesn't handle it
#$(info empty=>$(subst ,,)<) # empty

$(info 1 $(subst foo,bar,foobarbaz))
$(info 2 $(subst foo,bar,foo bar baz))
$(info 3 $(subst foo,bar,foo    bar     baz))  # WS preserved!
$(info 3 >>$(subst foo,bar,   foo    bar     baz    )<<)  # WS preserved!
$(info 3 >>$(strip $(subst foo,bar,   foo    bar     baz    ))<<)  # WS lost by strip()
3:=>>$(strip $(subst foo,bar,   foo    bar     baz    ))<<  # WS lost by strip()
$(info 3=$3)

# pattern strings with embedded spaces
$(info 1 spaces=$(subst foo bar baz,qqq,foo bar baz)) # qqq
foobarbaz=foo bar baz
$(info 2 spaces=$(subst foo bar baz,qqq,foo bar baz $(foobarbaz))) # qqq qqq

$(info empty=$(subst,z,a b c d e f g)) # empty string!? (weird)
$(info empty=$(subst ,z,a b c d e f g)) # a b c d e f gz  (wtf?)
$(info empty=$(subst ,z,a  b  c  d  e  f  g)) # a  b  c  d  e  f  gz  
$(info empty=$(subst ,z,  a  b  c  d  e  f  g  )) #  a  b  c  d  e  f  g  z
$(info empty=$(subst a,,a b c d e f g)) # b c d e f g  (remove a)
$(info empty=$(subst ,,a b c d e f g)) # a b c d e f g   (no change)

@:;@:

