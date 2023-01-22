$(info b=$(basename src/foo.c src-1.0/bar qux.c hacks))

# whitespace is consumed
$(info  b=$(basename  src/foo.c  src-1.0/bar  qux.c  hacks))

x=aa.a	bb.b	cc.c	dd.d	ee.e	ff.f	gg.g
$(info  x=$(basename  $x))

@:;@:

