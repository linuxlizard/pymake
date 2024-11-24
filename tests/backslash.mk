# How does GNU Make handle \'s as line continuation?
#
# davep 24-Sep-2014

# Manual 3.1.1 says:
# "Outside of recipe lines, backslash/newlines are converted into a single space
# character. Once that is done, all whitespace around the backslash/newline is
# condensed into a single space: this includes all whitespace proceding the
# backslash, all whitespace at the beginning of the line after the
# backslash/newline, and any consecutive backslash/newline combinations."
#
#
# TODO .POSIX will change the behavior of this file
#

# Don't use the shell because the shell will eat the whitespaces.  Make also
# preserves the leading whitespaces. 
SHELL=/bin/echo

all : test-backslash-semicolon test-backslash-recipes lots-of-fore-whitespace\
    lots-of-aft-whitespace backslash-in-string backslash-in-string-echo\
    backslash-eol backslash-o-rama backslash-space-eol assignment split-assignment \
    split-prereqs-with-backslashes this-is-a-rule-with-backslashes \
    backslash-in-comment rule-not-highlighted-by-vim \qqq \n \
foo foo foo foo  ; @echo $@ $^


# silent output without launching a shell
silent : SHELL=/usr/bin/touch
silent : ; @/dev/null
# Using test doesn't work. I don't know why. Always throws an error. Need to
# run GNU Make under the debugger. 
#silent : SHELL=/bin/test
#silent : ; @ 1 -eq 1

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
I_am_an_assignment_statement_=_\
that equals \ a bunch of stuff \ with \
backslashes \ that should not be \ confused with \
continuation \ of the \ line

assignment : 
	@echo $(I am an assignment statement)

# This works in older versions of Make. 
# The \ in LHS of assignment is ok.
# But fails in 3.82 and 4.0.
ifeq ($(MAKE_VERSION),3.81)
I_am_a_\
split_assignment = legal in 3.81 
endif

split-assignment : 
	@echo $(I am a split assignment)

# splitting RHS of rule (the prerequisites) parses ok
# The backslashed lines become 3 separate prereqs (the \ creates a space separated list of strings)
# "backslash-\space-\eol" becomes  "backslash-" "space-" "eol"  (three prereqs)
split-prereqs-with-backslashes : backslash-\
space-\
eol \
;\
@echo backslash-space-eol=>>$^<<

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

# I think "space" this winds up being an empty string. But the blank line after
# is confusing my backslash handling so this is a good test regardless
space=\

fake-out : this-$(space)is-$(space)a-$(space)rule-$(space)with-$(space)backslashes
	@echo $@

fake-out-2 : this- is- a- rule- with- backslashes
	@echo $@

$(info = @@space@@=@@space$(space)@@)

# from ffmpeg
# Note in the $(info) output all the extra spaces are collapsed into a single space
SUBDIR_VARS := CLEANFILES EXAMPLES FFLIBS HOSTPROGS TESTPROGS TOOLS      \
               HEADERS ARCH_HEADERS BUILT_HEADERS SKIPHEADERS            \
               ARMV5TE-OBJS ARMV6-OBJS VFP-OBJS NEON-OBJS                \
               ALTIVEC-OBJS VIS-OBJS                                     \
               MMX-OBJS YASM-OBJS                                        \
               MIPSFPU-OBJS MIPSDSPR2-OBJS MIPSDSPR1-OBJS MIPS32R2-OBJS  \
               OBJS HOSTOBJS TESTOBJS
#$(info $(SUBDIR_VARS))
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
	@echo \qqq=$@ \abc=$^

\n : \r
	@echo $@

\t : \g ; @echo backslash-t does what \\\
\\\
\\

slash-o-rama\
=\
foo\
bar\
baz\
blahblahblah
$(info = foo bar baz blahblahblah=$(slash-o-rama))

slash-o-rama-rule : SHELL=/bin/echo
slash-o-rama-rule : 
	@echo slash-o-rama=$(slash-o-rama)

embedded-slash-o-rama\ =\ foo\ bar\ baz\ blahblahblah
$(info = \ foo\ bar\ baz\ blahblahblah=$(embedded-slash-o-rama\))

embedded-slash-o-rama-rule : SHELL=/bin/echo
embedded-slash-o-rama-rule : 
	@echo embedded-slash-o-rama=$(embedded-slash-o-rama\)

# reserved symbols backslashable?
# \% -> % ?  Or just a literal "\%"
\% = percent
$(info = percent=$(\%))
%\ = percent
$(info = percent=$(%\))

# 3.1.1 Splitting Long Lines
#  "Outside of recipe lines, backslash/newlines are converted into a single
#  space character. Once that is done, all whitespace around the
#  backslash/newline is condensed into a single space: this includes all
#  whitespace preceding the backslash, all whitespace at the beginning of the
#  line after the backslash/newline, and any consecutive backslash/newline
#  combinations."
more-fun-in-assign\
=           \
    the     \
    leading \
    and     \
    trailing\
    white   \
    space   \
    should  \
    be      \
    eliminated\
    \
    \
    \
    including \
    \
    \
    blank\
    \
    \
    lines
$(info = the leading and trailing white space should be eliminated including blank lines=$(more-fun-in-assign))

# all these empty lines should be ignored 
many-empty-lines\
=\
    \
    \
    \
    \
\
\
\
                            \
\
    foo
$(info = foo=$(many-empty-lines))

# lone backslash (Trailing space after \ to make a literal \<space>
backslash-space = \ 
$(info = one backslash \ =one backslash $(backslash-space))

# two backslash (Trailing space after \ to make a literal \\<space>
two-backslash-space = \\ 
$(info = two backslash \\ =two backslash $(two-backslash-space))

# lone backslash with continuation
# XXX this should become two backslashes
literal-2-backslash = \\\
q
$(info = 1 \ q=1 $(literal-2-backslash))

# lone backslash with continuation (spaces before q are eaten)
# this is so weird. I'm getting lone \ for the two \\ when I expect to see two
# \\ (backslashes) output. Did I find a GNU make parser bug?
literal-2-backslash-spaces = \\\
        q
$(info = 2 \ q=2 $(literal-2-backslash-spaces))

# Do spaces after my \\ give me two \\ output? yes! WTF?
literal-2-backslash-more-spaces = \\   \
        q
$(info = 3 \\ q=3 $(literal-2-backslash-more-spaces))

# Leading backslash seems to violate GNU Make's manual.
# By the manual's rules there should be a space before foo.
leading-backslash\
=\
foo
$(info = 1 foo=1 $(leading-backslash))

leading-backslash-2\
=\
            foo
$(info = 2 foo=2 $(leading-backslash-2))

# there is a space between foo and bar but not before foo
leading-backslash-3\
=\
            foo\
            bar
$(info = 3 foo bar=3 $(leading-backslash-3))

SRC\
=\
hello.c\

$(info SRC=$(SRC))

# implicit "catch all" rule to trap busted rules 
% : ; @echo {implicit} $@

