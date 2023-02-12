# immediate
a:=10
$(info a=$a)

# recursively expanded variable
b=20
c=30
$(info b=$b c=$c)

d1=$a $b $c
d2:=$a $b $c
$(info d1=$(d1) d2=$(d2))

# change the value of b, c
b=40
c=50
$(info d1=$(d1) d2=$(d2))

# from the GNU Make 4.2 manual Jan 2020
foo = $(bar)
bar = $(ugh)
ugh = Huh?
$(info $(foo) $(bar) $(ugh))

FOO ?= bar
$(info FOO=$(FOO))

BAR:=bar
BAR ?= baz
$(info BAR=$(BAR))

# error "Recursive variable 'CFLAGS' references itself (eventually)"
#CFLAGS=-Wall -g
#CFLAGS=$(CFLAGS) -O
#$(info CFLAGS=$(CFLAGS))

# shell assign
uname!=uname -a
$(info uname=$(uname))

# POSIX make syntax of simply expanded assign
q::=q
r::=r
s::=s
$(info $q $r $s)


@:;@:
