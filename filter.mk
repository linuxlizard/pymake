# davep 20220902 ; let's figure out how GNU Make's filter() sees the world.

x:=aa aa aa aa aa aa aa aa aa aa aa bb

$(info   5   x=$(filter   $(strip $(x)) $(x) $(shell seq 1 10)aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy  zz,$(x)  bb bb bb aa aa  aa))
$(info 5 x=$(filter aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz,$(x) bb bb bb aa aa aa))
$(info 1 x=$(filter aa,$(x)))
$(info 2 x=$(filter aa,$(x) bb bb bb ))
$(info 3 x=$(filter aa,$(x) bb bb bb aa aa aa))
$(info 4 x=$(filter aa bb,$(x) bb bb bb aa aa aa))
$(info 5 x=$(filter aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz,$(x) bb bb bb aa aa aa))
$(info 6 x=$(filter $(x) bb bb bb aa aa aa,aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz))
$(info 7 x=$(filter aa,aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  bb))
$(info 7 x=$(filter aa,  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  bb   ))
$(info 7 x=$(filter aa aa,  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  bb   ))
$(info 7 x=$(filter aa,aa	aa	aa	aa	aa	aa	aa	aa	aa	aa	aa	bb))

a:=aa
$(info 8 x=$(filter $(a),$(x)))
b:=bb
$(info 9 x=$(filter $(a) $(b),$(x)))

$(info a x=$(filter $(a)$(b),$(x)bb $(x)b))

$(info b x=$(filter $(a), a))
$(info c x=$(filter aa,aa,aa,aa,aa,aa))

acomma=a,a
$(info acomma x=$(filter $(acomma),aa,aa,aa,aa,aa))
$(info acomma x=$(filter $(acomma),aa,aa aa,aa aa))
$(info acomma x=$(filter aa $(acomma),aa,aa aa,aa aa))

# confusing but I think Make is seeing this
# as filter "a" in ("a", ",", "a", ",", ... "a")
$(info x=>>$(filter aa, aa , aa , aa , aa , aa)<<)

comma=,
$(info comma x=$(filter $(comma),aa,aa,aa,aa,aa))
$(info comma x=$(filter $(comma),aa , aa , aa , aa , aa))

x=       aa    bb   cc    dd    ee   ff    gg 
$(info spaces x=$(filter aa bb,$x))
$(info spaces x=$(filter              aa      bb     ,     $x      ))
$(info spaces x=$(filter              aa      bb   $(comma)  ,     $x    $(comma) $(comma) ))

# wildcards
SRC=hello.c there.c all.c you.c rabbits.c lol.S foo.h
$(info cfiles=$(filter %.c,$(SRC)))
$(info hc=$(filter h%.c,$(SRC)))

$(info cS=$(filter %.c %.S,$(SRC)))

@:;@:

