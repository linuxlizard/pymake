# Fiddling with the info function.
#
# info, warning, error are allowed in contexts that other functions are not.
# (See also functions.mk)
#
# I can put an info/warning/error function as the only entry on a line. I can
# use info/warning as a function returning a null string.
#
# davep 07-Oct-2014 

$(info hello, world)

$(info Hello, world)$(info Hello, World) 

q$(info I am q)=42
$(info q=$q)

all:;@:

