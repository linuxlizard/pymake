# need a test that will always work correctly no matter what system runs the
# test and what code might change over time.
#
# use $(sort) on $(wildcard) to guarantee file order

pyfiles := $(wildcard functions*.py)
$(info pyfiles=$(pyfiles))

pyfiles := $(sort $(wildcard functions*.py))
$(info pyfiles=$(pyfiles))

pyfiles := $(sort $(wildcard functions*.py))
$(info pyfiles=$(pyfiles))

testfiles := $(sort $(wildcard test_* *.mk))
$(info testfiles=$(testfiles))

pattern=*.py
patternfiles := $(sort $(wildcard $(pattern)))
$(info patternfiles=$(patternfiles))

@:;@:

