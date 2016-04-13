# Fiddling with the info function.
#
# info, warning, error are allowed in contexts that other functions are not.
# (See also functions.mk)
#
# I can put an info/warning/error function as the only entry on a line. I can
# use info/warning as a function returning a null string.
#
# davep 07-Oct-2014 

$(info hello, world) $(info hello, world)
$(info hello, world)            $(info hello, world)

# two lines (info adds carriage return between calls)
$(info Hello, world)$(info Hello, World) 

# resolves to q=42
q$(info assigning to q)=42
$(info q=$q)

s=$(info hello, world)
$(info info returns s="$s")

a=
$(info a="$(value a)")
#a=
$(if $a,$(error foo),$(info ok))
#$(if "",$(error foo),$(info ok))
$(if ,$(error foo),$(info ok))

# should resolve to nothing (leading space is significant)
a=$( info leading space)
$(info a=>$a<)
$(if $( info leading space),$(error foo),$(info ok))


all:;@:

