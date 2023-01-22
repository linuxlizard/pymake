reverse = $(2) $(1)
foo = $(call reverse,a,b)

$(info foo=$(foo))
$(info $(call reverse,1,2,3,4,5))

# variable override
1:=q
$(info 1=$(1))
$(info $(call reverse,a,b))
$(info 1=$(1))
$(info $(call reverse,a))

# args start deep
#deeparg = $(suffix $(5))
deeparg = $(suffix $5)
$(info $(call deeparg,a.a,b.b,c.c,d.d,e.e,f.f))
# now using var instead of arg
5:=q.q
$(info $(call deeparg,a.a))

# call something that does not exist
$(info dave=$(call dave,a,b,c,d))

# are the args evaluated even if the cmd doesn't exist?
# yes. these files do exist.
a=$(shell echo a > /tmp/a.txt)
b=$(shell echo b > /tmp/b.txt)
c=$(shell echo c > /tmp/c.txt)
d=$(shell echo d > /tmp/d.txt)
$(info dave=$(call dave,$a,$b,$c,$d))

@:;@:


