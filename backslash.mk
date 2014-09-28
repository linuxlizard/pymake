# How does GNU Make handle \'s as line continuation?
#
# davep 24-Sep-2014

# Manual 3.1.1 says:
# "Outside of recipe lines, backslash/newlines are converted into a single space
# character. Once that is done, all whitespace around the backslash/newline is
# condensed into a single space: this includes all whitespace proceding the
# backslash, all whitespace at the beginning of the line after the
# backslash/newline, and any consecutive backslash/newline combinations."

# Don't use the shell because the shell will eat the whitespaces.  Make also
# preserves the leading whitespaces. 
SHELL=/bin/echo

all : test-backslash-semicolon test-backslash-recipes lots-of-fore-whitespace\
    lots-of-aft-whitespace backslash-in-string backslash-in-string-echo\
    backslash-eol backslash-o-rama backslash-space-eol assignment split-assignment \
    split-prereqs-with-backslashes this-is-a-rule-with-backslashes \
    backslash-in-comment rule-not-highlighted-by-vim \qqq \n \
 ; @echo $@ $^


test-backslash-semicolon : ; @echo $@ \
 qqqq

test-backslash-recipes : 
	@echo $@ \
 qqqq

# whitespace before is preserved
lots-of-fore-whitespace : 
	@echo $@ \
                                qqqq

# whitespace and after before qqq is preserved
# there is a lot of whitespace after the qqqq
lots-of-aft-whitespace : 
	@echo $@ \
                                qqqq                                

# uh oh \ in string will make my life difficult
# try with shell to see the printf (bonus: rule specific variable)
backslash-in-string : SHELL=/bin/sh
backslash-in-string : 
	@printf "foo%s bar%s baz%s \n" \
	@printf "FOO BAR BAZ\n" 

# back to using /bin/echo
backslash-in-string-echo: 
	@printf "foo bar baz\n" \
@printf "FOO BAR BAZ\n" 

# does Make need \<eol> or is it just the last \ on a line that makes it happy?
backslash-eol : 
	@echo $@ \
newline!

# space after backslash is error
# the following throws error "missing separator"
#backslash-space-eol : 
#	@echo $@ \ 
#newline!

# <tab>\    <-- starts the recipe, \ continues to next line
# <tab>\    <-- literal <tab> before \ is eaten (why?)
# <space>...<space>\\\\\\\  <-- six spaces then six \'s; seeing the leading
#                               spaces in the output
# \ <-- empty line
# \ <-- empty line
#     @echo $@  <--- leading spaces
#
# first <tab> starts the recipe, continues to next line
# next line is <tab>
backslash-o-rama : 
	@\
	\
      \\\\\\\
\
\
   @echo $@

# this works (spaces after backslash)
# because the recipes end. The \ becomes a literal \ in the string
backslash-space-eol : 
	@echo $@ \
space after this backslash!\  

# this works \ in RHS of assignment is ok
I am an assignment statement = \
that equals \ a bunch of stuff \ with \
backslashes \ that should not be \ confused with \
continuation \ of the \ line

assignment : 
	@echo $(I am an assignment statement)

# this works. \ in LHS of assignment is ok
I am a \
split assignment = is this legal?
split-assignment : 
	@echo $(I am a split assignment)

# splitting RHS of rule (the prerequisites) parses ok
# Error "no rule to make target 'backslash-'
split-prereqs-with-backslashes : backslash-\
space-\
eol \
;\
@echo $@

# GNU make successfully parses this with no complaints. Can't seem to hit it.
# for "this-is-a-rule-with-backslashes"
# Ah ha! is creating a rule with the targets: this- is- a- rule- with- backslashes
# 3.1.1 says" backslash/newlines are converted into a single space character"
this-\
is-\
a-\
rule-\
with-\
backslashes : ; @echo $@

space=\

fake-out : this-$(space)is-$(space)a-$(space)rule-$(space)with-$(space)backslashes
	@echo $@

fake-out-2 : this- is- a- rule- with- backslashes
	@echo $@

# from ffmpeg
# Note in the $(info) output all the extra spaces are collapsed into a single space
SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS      \
               HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS            \
               ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS                \
               ALTIVEC-OBJS VIS-OBJS                                     \
               MMX-OBJS YASM-OBJS                                        \
               MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS  \
               OBJS HOSTOBJS TESTOBJS
$(info $(SUBDIR_VARS))
subdir_vars : $(SUBDIR_VARS)

# from Linux kernel 3.12.5 (removed the 'rm' so it's not dangerous)
# (plus this makefile uses SHELL=/bin/echo so it's doubly not dangerous)
clean: $(clean-dirs)
#	$(call cmd,rmdirs)
#	$(call cmd,rmfiles)
	@find $(if $(KBUILD_EXTMOD), $(KBUILD_EXTMOD), .) $(RCS_FIND_IGNORE) \
		\( -name '*.[oas]' -o -name '*.ko' -o -name '.*.cmd' \
		-o -name '*.ko.*' \
		-o -name '.*.d' -o -name '.*.tmp' -o -name '*.mod.c' \
		-o -name '*.symtypes' -o -name 'modules.order' \
		-o -name modules.builtin -o -name '.tmp_*.o.*' \
		-o -name '*.gcno' \) -type f -print | xargs 

# use this shell on this so can tinker with the prerequisites
backslash-in-prereqs : SHELL=/bin/sh
backslash-in-prereqs : a\
b\
c\
d\
        e\
    f
	@for t in $^ ; do echo $$t ; done
	@for t in $^ ; do echo $(addprefix @@,$$t) ; done

backslash-in-comment : # this is a comment \
does this continue the comment?\
how about now?\
seems like it does\

rule-not-highlighted-by-vim : ; @echo $@
# the trailing \ on the backslash-in-comment is confusing vim but gnu make
# seems happy with it

# backslash in rules/prereqs?
\qqq : \abc
	@echo $@

\n : \r
	@echo $@

\t : \g ; @echo \\\
\\\
\\

# implicit "catch all" rule to trap busted rules 
% : ; @echo {implicit} $@

