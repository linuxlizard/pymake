# should be 'undefined'
$(info $(origin .SHELLSTATUS))

FOO := $(shell echo foo)

# will now be 'override' (not sure why GNU Make chose that value)
$(info $(origin .SHELLSTATUS))

ifneq ($(.SHELLSTATUS),0)
$(error .SHELLSTATUS == $(.SHELLSTATUS))
endif

BAR != echo bar
$(info $(origin .SHELLSTATUS))
ifneq ($(.SHELLSTATUS),0)
$(error .SHELLSTATUS == $(.SHELLSTATUS))
endif

ERROR != exit 1
$(info $(origin .SHELLSTATUS))
ifneq ($(.SHELLSTATUS),1)
$(error .SHELLSTATUS == $(.SHELLSTATUS))
endif

# recursive variable
BAZ = $(shell echo baz)
export BAZ

$(info BAZ=$(BAZ) $(origin .SHELLSTATUS))
ifneq ($(.SHELLSTATUS),0)
$(error .SHELLSTATUS == $(.SHELLSTATUS))
endif


@:;@:

