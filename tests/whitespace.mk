# TODO pymake cannot yet parse this file

# the next line is $<space>  (gnu make ignores as of v4.3)
$ 

# the next line is $<tab>  (gnu make ignores as of v4.3)
$	

# gnu make accepts and ignores these
$()
$( )
$(info $())

$( )foo=fooA
$(info $$foo=$($( )foo)  qq   )

x:=a a a a a a a a a a a  a a a  a a a b

a=a
b=b

xx=$x $x

$(info $a$b $a $b $(xx) q q q   $b    $a  $(shell seq 1 10 ) $a$(shell seq 2 2 12)$a ,  $(x)b $(x)a 1 2 3 4 )
$(info $(filter       $a$b $a $b $(xx)  q qq qqq   $b    $a  $(shell seq 1 10 ) $a$(shell seq 2 2 12)$a ,  $(x)b $(x)a 1 2 3 4 ))

# argv[0] == 
# "ab a b a a a a a a a a a a a  a a a  a a a b a a a a a a a a a a a  a a a  a a a b  q q q   b    a  1 2 3 4 5 6 7 8 9 10 a2 4 6 8 10 12a "
# argv[1] ==
# "  a a a a a a a a a a a  a a a  a a a bb a a a a a a a a a a a  a a a  a a a ba 1 2 3 4 "
#

# dangling varref $<space>
foo=bar $ 
$(info foo=$(foo))

# *** empty variable name. Stop.
# = bar

# leading whitespace is preserved
# trailing whitespace is discarded
FOO:=   BAR   
$(info FOO=>>>$(FOO)<<<)

@:;@:

