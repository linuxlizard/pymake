# make 3.81 "export define" not allowed ("missing separator")
# make 3.82 works
# make 4.0  works
export define foo
bar
endef
$(info $(call foo))

@:;@:

