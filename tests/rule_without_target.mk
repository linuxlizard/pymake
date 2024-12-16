FOO:=1

# because we haven't seen a Recipe yet, this is treated as just a regular line.
	ifdef FOO
    $(info FOO=$(FOO))
endif

# "rule without a target" for
# "compatibility with SunOS 4 make"
: foo
	echo error\! should not see this
	exit 1

foo:
ifdef FOO
	@echo foo
endif

