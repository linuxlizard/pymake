# Need a simple command that will give me the same response every time.
# From the date man page:
DATE:=date --date='TZ="America/Los_Angeles" 09:00 next Fri'

# Example of loops in recursive variable references: ECHO requires value of NOW
# but the $(shell) for NOW also requires ECHO.  The 'printenv' exit value is
# non-zero when the var doesn't exist. But under GNU Make 'ECHO' env var does
# exist so we see 'ok' in the output. The value of NOW in ECHO will be an empty
# string.
#
NOW = $(shell $(DATE) ; printenv ECHO && echo ok)
ECHO = $(shell echo NOW is __$(NOW)__)


export NOW ECHO

$(info NOW=$(NOW))
$(info ECHO=$(ECHO))

@:;@:
	printenv ECHO
	printenv NOW 

