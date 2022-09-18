x=a b c d e f g
$(info $(strip $x))

x=a  b  c  d  e  f  g
$(info $(strip $x))

x=  a  b  c  d  e  f  g    # spaces at end
$(info $(strip $x))
$(info $(strip $x $x $x))
$(info $(sort $(strip $x $x $x)))
$(info $(filter a e,$(sort $(strip $x $x $x))))

x=		a		b		c		d		e		f		g				
$(info $(strip $x))

x:=
$(info >>$(strip )<<)
$(info >>$(strip 				)<<)

@:;@:

