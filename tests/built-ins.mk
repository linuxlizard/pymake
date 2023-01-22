# peek at GNU Make's built-in variable names
#
# Also run with -R  "Disable the built-in variable settings"

$(info .VARIABLES=$(.VARIABLES))

# as of GNU Make 4.3
BUILTIN:=.VARIABLES .LOADED .INCLUDE_DIRS .SHELLFLAGS .DEFAULT_GOAL\
  .RECIPEPREFIX .FEATURES VPATH SHELL MAKESHELL MAKE MAKE_VERSION MAKE_HOST\
  MAKEFLAGS GNUMAKEFLAGS MAKECMDGOALS CURDIR SUFFIXES .LIBPATTERNS\

$(foreach var,$(BUILTIN),$(info $(var)=$($(var)) from $(origin $(var))))

@:;@:
