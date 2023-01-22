# need a test that will always work correctly no matter what system runs the
# test and what code might change over time.
#
# use $(sort) on $(wildcard) to guarantee file order

pyfiles := $(sort $(wildcard functions*.py))
$(info pyfiles=$(pyfiles))

pyfiles := $(sort $(wildcard ../pymake/*.py))
$(info pyfiles=$(pyfiles))

pattern=*.py
files := $(sort $(wildcard $(pattern)))
$(info files=$(files))

@:;@:
