# error empty variable name
#define

define simple-assign :=
	@echo abc
	@echo 123
endef

define default-assign
	@echo def
	@echo 456
endef

define append-assign +=
	@echo hij
	@echo 789
endef

define recursive-assign = 
	@echo klm
	@echo 101112
endef

define shell-assign !=
	uname -a ;
	which uname
endef

t=t
l=l

# warning: extraneous text after 'define' directive
define $two$lines = q
	echo foo
	echo $(BAR)
endef

# ooooo interesting the blank line here is preserved
# (without it, the echo $(BAR) echo $(BAZ) are on the same line
# and are treated as echo "$(BAR) echo $(BAZ)"  (2nd echo is a literal string
# to the 1st echo)
define twolines += 
	
	echo $(BAZ)
endef


	define tab-indent-assign
	echo oh tab where else can you sneak in
endef

	define	tab-define-tab-assign
	echo tab-define-tab
endef

$(info $(filter %-assign,$(.VARIABLES)))

all:
	$(twolines)

shell:
	@echo "$(shell-assign)"

