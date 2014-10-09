# Only function calls. What happens?
#
# davep 07-Oct-2014 ;

$(info hello, world)

$(if "$(FOO)",$(BAR),$(BAZ))

$(info hello, world)

$(info $(.FEATURES))

$(warning warning warning danger danger!)

$(sort foo bar lose)

#$(foreach prog

#$(subst from,to,text)

#$(or a,b,c)
#$(and a,b,c)

#$(dir ./tests)

#$(shell ls)

#$(join a b,.c .o)

# need to have one target to prevent make from complaining
all:;@:

