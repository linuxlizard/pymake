#
# Test various horrible things that can happen on the LHS of an Assignment or Rule
#   
#   Assignment  ::= LHS assignment_op RHS
#   Rule        ::= LHS rule_op RHS
#
#   assignment_op = {"=","?=",":=","::=","+=","!="}
#   rule_op = { ":", "::" }
#
# The statement tokenizer reads LHS until finds [assignment_op | rule_op].
# This Makefile tests how assignments and rules are similar/different.
#
# Is there any case where a LHS between Assignment and Rule are ambiguous?
# Can I put an assignment_op into the LHS of a rule? 
# Can I put a rule_op into the LHS of an assignment?
#
# Here's a tough case:
#   this is a test = foo  --> ("this is a test","=","foo")
#   this is a test : foo  --> ("this","is","a","test",":","foo")
#
# Spaces must be preserved until the rule vs assignment has been
# disambiguated.
#
# 
#
# davep 15-sep-2014

# this is a comment
$(CC)=gcc

all:a\=b ; @echo all

backslash=\

\?==foo
$(info = foo=$($(backslash)?))

\+=+
$(info @ +@$(+))

# error "empty variable name"
#+=+
#$(info @ +@$(+))

# error "empty variable name"
#===

# empy RHS -- ok
empty1=
empty2?=
empty3:=
empty4::=
empty5+=
empty6!=

equal==
$(info @ =@$(equal))

# variable assignment masquerading as variable LHS
!==qq
$(info @ !@$(!$(equal)))

a$(equal)b : c ; @echo a=b

$(info @ a=b@a=b)

# raw equal doesn't work as a prerequisite
# error "empty variable name"
#= : ; @echo $@
$(equal) : ; @echo @=@$@

# target "empty7" with prerequisite of "="
empty7 : = ; @echo $@

# This parses. But what does it do?
empty7 :\ = ; @echo empty8
$(info = @echo empty8=$(empty8 : ))

empty7 := ; @echo empty7
$(info = ; @echo empty7=$(empty7))

c:;@echo c

# aw crap
this is a test = foobarbaz
this is a test : foobarbaz

    lots of leading spaces = aw yis leading spaces
$(info = aw yis leading spaces=$(lots of leading spaces))
lots of trailing spaces     = hell yeah trailing spaces
$(info = hell yeah trailing spaces=$(lots of trailing spaces))
ok more trailing spaces on rhs = there are six trailing spaces after this last .      
$(info = there are six trailing spaces after this last .      =$(ok more trailing spaces on rhs))
leading spaces are ignored I'm sorry to say  =      all these leading spaces are ignored
$(info = all these leading spaces are ignored=$(leading spaces are ignored I'm sorry to say))

# this parses
? = question
$(info = question=$(?))
+ = plus
$(info = plus=$(+))
* = star
$(info = star=$(*))
~`@$$*!&%\:::=a mess
$(info = a mess=$(~`@$$*!&%\:))

$(this is a test) : ; @echo = foobarbaz=$(this is a test)

hello\ $(this is a test) = $(hello $(this is a test))
hello\ $(this is a test) : $(hello  $(this is a test)) ; @echo = hello foobarbaz=hello foobarbaz

%:;@echo {implicit rule} $@

