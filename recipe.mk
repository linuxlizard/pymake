# Tinker with recipes. 
# davep 23-Sep-2014

#
# Oh ho. "missing separator" means GNU Make treating :,:: and assignment tokens as separator!
#

# where do recipes end?
all : 
# this is a comment
	@echo = all=$@
# blank line after this comment

	@echo = $@ again=$@ again
# recipe continues
	# this is passed to the shell

# recipe ends where?
	echo : echo # looks like rule, valid shell


   foo=bar # recipe definitely ends here
	# empty line with tab is ignored

# tab then something throws an error "commands commence before first target."
#	echo foo

backslashes : ; @echo back\
slash

# tab before "slash2"
backslashes2 : ; @echo back\
	slash2

# slaces before slash3b
backslashes3 : ; @echo back\
slash3
	@echo back\
        slash3b
# lots of leading spaces collapsed to one space
	@echo back\
                                        slash3c

where-do-i-end : ; @echo $@
	@echo leading tab
# leading spaces error "missing separator" 
#    @echo bar
	@echo I am still in $@

    # comment with leading spaces; part of recipe
	@echo yet again I am still in $@
    foofoofoo=999 # recipe is done here; leading spaces are ignored (eaten by recipe tokenizer?)
$(info = 999=$(foofoofoo))    # leading spaces on name are ignored


whitespace-then-tab : ; @echo $@
    
# leading whitespace then tab is not valid error "missing separator"
#    	@echo lots of leading whitespace here


varrefs : ; @echo $@
# the $(info) is error "commands commence before first target"
#$(info inside varref recipes)
	@echo varref recipe
# this $(info) is not executed (not seeing the message)
	@echo varref recipe info=$(info inside varref recipes)
# this $() is executed (seeing the date)
	@echo varref recipe date=$(shell date)
    # this $(error IS hit) (this comment is valid but Vim highlights as error)
	@echo varref recipe info=$(error inside varref recipes)

end-of-varrefs=yeah this ends varrefs rule for sure


spaces-in-weird-places : ; @echo = spaces-in-weird-places=$@

# the next line starts with a raw <tab>. Is valid. (starts empty shell? ignored?)
	

# the next line is <space><tab><EOL>. Is valid. (ignored)
 	

# the next line starts with a raw <tab>. Is valid. (Sent to shell)
	foo=bar printenv "foo"

	@echo I am still inside $@

# the next line is <tab><tab>. Is valid. The tabs are eaten.
		@echo tab tab

# the next line is <tab><space><tab>. Is valid. The tabs/spaces are eaten.
	 	@echo tab space tab

# the next line is <tab><space><tab><space><space><space>. Is valid. The tabs/spaces are eaten.
	 	   @echo tab space tab space space space

# the next line is has trailing <tab>s and <space>s; can see the whitespace on a hexdump of this output
# the trailing whitespace is preserved
	@echo I have trailing whitespacespaces                  	   	

# this line ends the recipe; note can be interpretted as either an assignment or a shell recipe
 	foo=bar printenv "foo"
$(info = bar printenv "foo"=$(foo))

whitespace-error : ; @echo $@
# the next line is <space><tab> then the echo
# error "missing separator"
# 	@echo space tab

# error "missing separator"
#foo bar baz

ifdef foo
endif

# Need to avoid confusion between recipe trailing rule with ';' and the recipes
# on the next line
# This is not valid.
#weird-semicolon:
#; @echo $@

