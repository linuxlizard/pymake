$(info $(sort z y x b c a))
$(info  $(sort  z  y  x  b  c  a))
$(info		$(sort		z		y		x		b		c		a))

x=x
y=y
z=z
$(info $(sort a $x b $y c $z))

$(info $(sort a $x $x b $y $y c $z $z))
$(info $(sort a $x$x b $y$y c $z$z))

$(info $(sort $(shell cat /etc/passwd)))

$(info $(sort $(wildcard *.py)))

$(info $(sort $(sort a $x $x b $y $y c $z $z)))

@:;@:

