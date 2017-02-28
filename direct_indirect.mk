# direct and indirect assignment
path:=$(PATH)
split_path=$(subst :, ,$(path))
$(info $(split_path))
path=foo:bar:baz:
$(info $(split_path))
path=a:b:c
$(info $(split_path))

@:;@:

