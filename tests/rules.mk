#  Test GNU Make capabilities.
#  davep 13-Sep-2014
#
#  Handling of $() variable reference substitutions is done differently in
#  rules than in statements. I need to read the manual some more. 

all: foo

foo:
	@touch bar

foo2:   # hello there; is this comment ignored?
	@touch bar2

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
\\ : ; @echo I am backslash $@

# make -f rules.mk ! --> !
! : ; @echo I am bang $@

# prerequisite with embedded spaces
# make -f rules.mk "I have spaces" -> I have spaces
I\ have\ spaces : ; @echo $@
# make -f rules.mk "I have three spaces" -> I   have   three   spaces
I\ \ \ have\ \ \ three\ \ \ spaces : ; @echo $@
# make -f rules.mk "I have trailing spaces" -> I have trailing spaces   
I\ have\ \trailing\ spaces\ \ \ : ; @echo $@

# prereqs with escaped :
# make -f rules.mk "I have a :" --> I have a :
I\ have\ a\ \: : ; @echo $@
# make -f rules.mk -n "I have a ;" --> echo I have a ;
I\ have\ a\ \; : ; @echo $@

# make CC=gcc LD=ld OBJ=hello.o -f rules.mk Igcchaveldembeddedhello.ovarref -> IGCChaveLDembeddedHELLO.Ovarref
I$(CC)have$(LD)embedded$(OBJ)varref : ; @echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))

# TODO still trying to figure out how to hit this rule
$$=42
I$$have$($$)embedded$($$)dollars : ; @echo $@

# make -f rules.mk 'I have42embedded42dollars' --> I have 42embedded42dollars
# make -f rules.mk 'I@@@@@@ have42embedded42dollars' --> I@@@@@@have 42embedded42dollars
$$=42
I%have$($$)embedded$($$)dollars : ; @echo $@

# make -f rules.mk 'I have embeddedqpercents' --> I have embeddedqpercents
# make -f rules.mk -r 'I have embeddedqqqqqqqqqpercents' --> I have embeddedqqqqqqqqqpercents
I\ have\ embedded%percents : ; @echo $@

# make -f rules.mk @ --> :
@:;@:
	exit 1

# TODO I have no idea WTF this is
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

# This parses. Don't know what it means.
: 

.PHONY : clean
clean:
	$(RM bar colon2 colon3 colon4)

# 4.2 Types of Prerequisites 
# "Order-only prerequisites can be specified by placing a pipe symbol (|) in
# the prerequisites list: any prerequisites to the left of the pipe symbol are
# normal; any prerequisites to the right are order-only:"
OBJDIR := objdir
OBJS := $(addprefix $(OBJDIR)/,foo.o bar.o baz.o)
$(OBJS): | $(OBJDIR)
$(OBJS2): foo | $(OBJDIR)

$(OBJDIR):
	mkdir $(OBJDIR)

# 4.11 Static Pattern Rules
$(filter %.o,$(files)): %.o: %.c
	$(CC) -c $(CFLAGS) $< -o $@

# "‘%’ characters in pattern rules can be quoted with preceding backslashes (‘\’)."
#the\%weird\\%pattern\\ : target-pattern% : prereq-pattern%
#abc% : abcd% : %xyz

# 4.12 Double-Colon Rules
# https://stackoverflow.com/questions/7891097/what-are-double-colon-rules-in-a-makefile-for
double-colon1 :: colon2
	@touch double-colon1-colon2
double-colon1 :: colon3
	@touch double-colon1-colon3
double-colon1 :: colon4
	@touch double-colon1-colon4

colon2:;@touch colon2
#colon2:;@touch colon2-b
colon3:;@touch colon3
colon4:;@touch colon4

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

# semicolon here is invalid (that's a surprise)
#rule-with-; : ; @echo $@

# ok
rule-with-! : ; @echo $@

# this is OK
empty-recipe : ; 

# implicit rules need careful study
# make -f rules.mk anything --> anything
%:;@echo {implicit rule} $@

