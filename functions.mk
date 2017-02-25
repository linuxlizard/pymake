# Only function calls. What happens?
#
# davep 07-Oct-2014 ;

$(info hello, world)

# legal (see "missing separator" notes below)
$(if "$(FOO)",$(BAR),$(BAZ))

$(info hello, world)

$(info $(.FEATURES))

$(warning warning warning danger danger!)

foo=$(sort foo bar lose)

#$(foreach prog

feet=$(subst ee,EE,feet in the street)

# NOT LEGAL -- "*** missing separator.  Stop."
# Seems to require a LHS. 
#$(sort foo bar lose)
#$(or a,b,c)
#$(and a,b,c)
# Many more; need to have tests for all of them.

a=$(or a,b,c)
b=$(and a,b,c)

c=$(dir ./tests)

d=$(shell ls)

e=$(join a b,.c .o)

# need to have one target to prevent make from complaining
@:;@:
