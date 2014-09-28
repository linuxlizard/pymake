# trailing spaces throw off backslashes

# the 
many-empty-lines\
=\
    \  
foo
$(info = foo=$(many-empty-lines))

