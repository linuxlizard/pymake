ifeq ($(MAKE_VERSION),3.81)
    should not ever execute this
endif

# For reference: GNU Make 4.3 
# conditional_line() - read.c

a,b = 42
$(info a,b=$(a,b))

ifeq ($(a,b),a,b)
$(error gnu make doesn't see this)
endif

ifeq ($(a,b),$(a,b))
$(info ifeq true)
$(info $$(a,b),$$(a,b))
endif

#
# Searching for how GNU Make treats whitespaces between the args
# (arg1,arg2)
# 

# GNU Make 4.3
# ***************************
#  leading spaces on 1st arg are preserved
# trailing spaces on 1st arg are discarded
#  leading spaces on 2nd arg are discarded
# trailing spaces on 2nd arg are preserved
# ***************************

# This looks like it should match.
# Trailing space problem
ifeq (a b ,a b )
$(error gnu make doesn't see this)
endif

ifeq (a b ,a b)
$(info (a b ,a b))
endif

# no match
ifeq (a b,a b )
$(error gnu make doesn't see this)
endif

# leading spaces on 1st arg are preserved
ifeq ( ab,ab)
$(error gnu make doesn't see this)
endif

# leading spaces on 1st arg are preserved
# leading spaces on 2nd are are discarded
ifeq ( ab, ab)
$(error gnu make doesn't see this)
endif

ifeq ( ab,ab )
$(error gnu make doesn't see this)
endif

ifeq ( ab, ab )
$(error gnu make doesn't see this)
endif

ifeq ( ab , ab )
$(error gnu make doesn't see this)
endif

# Note space after the comma. It's ignored.
# Spaces between characters are treated as part of the token.
ifeq (a b, a b)
$(info a b)
endif

# how are embedded commas treated?
a=b,a,b
ifeq ($a,b,a,b)
$(info ($$a,b,a,b))
endif

# extraneous text after 'ifeq' directive
#ifeq (a,a),
#endif


# "Invalid syntax in conditional."
# try to match "(" == "(" which
#ifeq ((,()
#endif

# obviously this should be fine
paren=(
ifeq ($(paren),$(paren))
$(info (paren,paren))
endif

# parse error (missing space after ifeq) that GNU Make reports as "missing separator"
#ifeq(1,1)
#endif

# "invalid syntax in conditional"
#ifeq ((1,1))
#endif

@:;@:

