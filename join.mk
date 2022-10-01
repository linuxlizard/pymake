$(info $(join a b,.c .o))

$(info $(join a b c d e f g ,.c .o))

$(info $(join a b ,.c .o .f .pas .cc .rs .ada))
$(info	$(join	a	b	,.c	.o	.f	.pas	.cc	.rs	.ada))
$(info     $(join     a     b     ,.c     .o     .f     .pas     .cc     .rs     .ada    ))

a=a
b=b
c=c
$(info $(join $a $b $c,$a $b $c))
a=aa aa
b=bb bb
c=cc cc
$(info $(join $a $b $c,$a $b $c))

# "This function can merge the results of the dir and notdir functions, to produce
# the original list of files which was given to those two functions." 
# -- GNU Make manual 4.3 Jan 2020

filenames=/etc/passwd /etc/shadow /etc/group
$(info $(join $(dir $(filenames)), $(notdir $(filenames))))

@:;@:

