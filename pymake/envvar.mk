# test for environment variables

# Good to know.  From GNU Make src/main.c:
# /* By default, export all variables culled from the environment.  */
#

path = $(PATH)
$(info path=$(PATH))
$(info path=$(subst :, ,${PATH}))

$(foreach dir,\
	$(subst :, ,$(PATH)),\
	$(info dir=$(dir))\
)

@:;@:

