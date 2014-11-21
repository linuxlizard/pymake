
# "Specify the search path directories for file names that match pattern."
vpath %.h ../headers

# "Clear out the search path associated with pattern."
vpath %.h

# "Clear all search paths previously specified with vpath directives"
vpath

# this is valid for some reason (not sure what happens inside Make)
vpath a=b
vpath a:=b

# assignment of var named "vpath"
vpath=42
ifndef vpath
$(error vpath should be a variable)
endif
ifneq ($(vpath),42)
$(error vpath != 42)
endif

include smallest.mk

