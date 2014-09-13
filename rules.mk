#  Test GNU Make capabilities.
#  davep 13-Sep-2014
#
#  Handling of $() variable reference substitutions is done differently in
#  rules than in statements. I need to read the manual some more. 

all: foo

foo:
	@touch bar

# whitespace in rules is different
the quick brown fox jumped over lazy dogs : ; @echo $@

# make -f rules.mk $(seq 7) --> 1\n2\n3\n4\n5\n6\n7
1 2 3 4 5 6 7 : ; @echo $@

# leading/trailing whitespace ignored
# make -f rules.mk $(seq 8 11) --> 8\n9\n10\n11
   8  9   10     11     : ; @echo $@

# quoted strings as target
#
# make -f rules.mk '"foo"'  --> echo "foo"
"foo" : ; @echo $@

# seems to break into three prereqs: ( "foo, bar, baz" )
# has trouble with the shell and the misbalanced quotes
# make -f rules.mk -n '"foo' bar 'baz"'  --> echo "foo\necho qqq\necho baz"
"foo qqq baz" : ; @echo $@

# backslashes treated like any other char in prereqs
# make -f rules.mk -n '\foo' --> echo \foo
\foo : ; @echo $@

# make -f rules.mk -n '$$' --> echo $$
$$$$ : ; @echo $@

# so \\ -> \ (literal backslash)
# shell wins up treating as empty echo?
# make -f rules.mk -n '\' --> echo \ 
\\ : ; @echo $@

# make -f rules.mk ! --> !
! : ; @echo $@


# make -f rules.mk @ --> :
@:;@:

.:;@.

# make -f rules.mk -n backslash --> echo \ 
backslash : \ 

# hurray for unicode!
# make -f rules.mk ಠ_ಠ --> I disapprove
ಠ_ಠ : ; @echo I disapprove
	
# resolves to b=a; echo $$$b is b
# make -f rules.mk -n b --> b=a; echo $$$b is b
a=b
$(a) : ; @b=a ; echo $$$$$$$a is $a

# make -f rules.mk : --> backslash : = : 
\: : ; @echo backslash : = $@

# this parses. No idea how to hit it. :: rules are special in GNU Make
: : ; @echo regular $@

export IAM=GROOT
override IAM=GROOT

.PHONY : clean
clean:
	$(RM bar)

# 6.21 Target-Specific Variable Values
prog : CFLAGS = -g
prog : export IAM = Groot
prog : override IAM2 = Groot2
prog : private IAM3 = Groot3
prog : prog.o foo.o bar.o
	@echo $(CFLAGS) $@
prog.o foo.o bar.o : 
	@echo $@
	@touch $@

# 6.12 Pattern Specific 

# 10.5 Pattern Rule
%.o : %.c 
	@echo $@

# 10.5.2 Pattern Rule Example
%.tab.c %.tab.h: %.y
	bison -d $<

# "The double colon makes the rule terminal, which means that its prerequisite
# may not be an intermediate file (see Section 10.5.5 [Match- Anything Pattern
# Rules], page 123)."
% :: RCS/%,v
	$(CO) $(COFLAGS) $<

# implicit rules need careful study
# make -f rules.mk anything --> anything
%:;@echo {implicit rule} $@

