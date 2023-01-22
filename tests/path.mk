$(info $(PATH))
path=$(PATH)
$(info path=$(path))

path=$(subst :, ,$(PATH))
$(info $(path))
#
#$(info $(notdir $(path)))
#$(info $(dir $(path)))

@:;@:
