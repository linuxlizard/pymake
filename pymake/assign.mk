a:=10
ifdef DEFER
b=$a  # delayed assignment ("b=20" below)
else
b:=$a  # immediate assignment  ("b=10" below)
endif
a:=20

$(info a=$(a) b=$(b))

# no output until a is eval'd
a=$(shell date)
$(info $(value a))
#$(if $a,$(error fail!),$(info a all good, man))

$(info a=**$(a)**)
a:=$(shell date)
$(if "$a",$(error fail!),$(info a all good, man))

@:;@:
