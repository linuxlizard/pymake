bar=bar
# two-lines is from the GNU Make manual
define two-lines 
	@echo two-lines foo
	@echo two-lines $(bar)
endef

define echo-stuff
	echo foo
	echo bar
	echo baz
endef

# the extra leading tabs/spaces are all eaten
define multi-line-define
	@echo this\
		  is\
		    a\
		multi-line\
		          define
endef

# This macro could be an error because the trailing spaces after the backslash
# breaks the macro being a multi-line. If the \<space> is incorrectly treated
# as a continuation, then the entire output will contain the extra "echo"
# strings. When the \<space> is properly ignored, the block will be multiple
# separate shell calls.
#
define trailing-spaces-define
	@echo this\ 
	   echo line \ 
	   echo has \ 
	   echo spaces \ 
	   echo after \ 
	   echo the backslashes
	  @echo for shame   
endef

define mixed-backslashes
	@echo this\
		line\
		is\
		backslashed
	@echo this line is not
	@echo but\
		this\
		line\
		is\
		again\
		backslashed
endef

all: test1 test2 test3 test4 test5 test6 test7

test1:
	echo this\
 is\
 a\
 shell\
 continuation

test2:
	$(two-lines)

test3:
	$(echo-stuff)

test4:
	echo this
	echo is
	echo multiple
	echo lines

test5:
	$(multi-line-define)

test6:
	$(trailing-spaces-define)

test7:
	$(mixed-backslashes)
