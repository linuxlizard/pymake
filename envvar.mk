# test for environment variables

path = $(PATH)
$(info path=$(PATH))
$(info path=$(subst :, ,${PATH}))

$(foreach dir,\
	$(subst :, ,$(PATH)),\
	$(info dir=$(dir))\
)

@:;@:

