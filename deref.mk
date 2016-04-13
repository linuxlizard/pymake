# Is there any way to deref something into a function call?
# So far, doesn't seem like it. Which will make my evaluate much much simpler
# but makes make less powerful, IMO.
info foo=99
a=info
#$(info$(call $a, foo))
#
#$(call $a,foo)

# intuitively these lines should be the same (hint: they're not)
$(info **$(info foo)**) # foo\n****
$(info **$($(a) foo)**) # **99**
    
# this is how a is deref'd to info
$(call $(a),this is from $$call)

# function call not the above "info foo" variable
$(info foo)

# if I ever get a tattoo, i'll have this on my butt.
@:;@:

