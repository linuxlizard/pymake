# legal
#ifdef: ; @echo $@

# not legal
#ifdef : ; @echo $@

# legal
#   ifdef:;@echo $@

# legal
#ifdef = 42
#$(info $(ifdef))

ifdef foo
$(error foo)
endif

# legal
ifdef=54
$(info $(ifdef))

# legal
#ifdef:=42

@:;@:

