x:=aa aa aa aa aa aa aa aa aa aa aa bb

$(info   5   x=$(filter-out   $(strip $(x)) $(x) $(shell seq 1 10)aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy  zz,$(x)  bb bb bb aa aa  aa))
$(info 5 x=$(filter-out aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz,$(x) bb bb bb aa aa aa))
$(info 1 x=$(filter-out aa,$(x)))
$(info 2 x=$(filter-out aa,$(x) bb bb bb ))
$(info 3 x=$(filter-out aa,$(x) bb bb bb aa aa aa))
$(info 4 x=$(filter-out aa bb,$(x) bb bb bb aa aa aa))
$(info 5 x=$(filter-out aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz,$(x) bb bb bb aa aa aa))
$(info 6 x=$(filter-out $(x) bb bb bb aa aa aa,aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp qq rr ss tt uu vv ww xx yy zz))
$(info 7 x=$(filter-out aa,aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  bb))
$(info 7 x=$(filter-out aa,  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  bb   ))
$(info 7 x=$(filter-out aa aa,  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  aa  bb   ))
$(info 7 x=$(filter-out aa,aa	aa	aa	aa	aa	aa	aa	aa	aa	aa	aa	bb))

a:=aa
$(info 8 x=$(filter-out $(a),$(x)))
b:=bb
$(info 9 x=$(filter-out $(a) $(b),$(x)))

$(info a x=$(filter-out $(a)$(b),$(x)bb $(x)b))

$(info b x=$(filter-out $(a), a))
$(info c x=$(filter-out aa,aa,aa,aa,aa,aa))

acomma=a,a
$(info acomma x=$(filter-out $(acomma),aa,aa,aa,aa,aa))
$(info acomma x=$(filter-out $(acomma),aa,aa aa,aa aa))
$(info acomma x=$(filter-out aa $(acomma),aa,aa aa,aa aa))

# confusing but I think Make is seeing this
# as filter-out "a" in ("a", ",", "a", ",", ... "a")
$(info x=>>$(filter-out aa, aa , aa , aa , aa , aa)<<)

comma=,
$(info comma x=$(filter-out $(comma),aa,aa,aa,aa,aa))
$(info comma x=$(filter-out $(comma),aa , aa , aa , aa , aa))

x=       aa    bb   cc    dd    ee   ff    gg 
$(info spaces x=$(filter-out aa bb,$x))
$(info spaces x=$(filter-out              aa      bb     ,     $x      ))
$(info spaces x=$(filter-out              aa      bb   $(comma)  ,     $x    $(comma) $(comma) ))

# wildcards
SRC=hello.c there.c all.c you.c rabbits.c lol.S foo.h
$(info cfiles=$(filter-out %.c,$(SRC)))
$(info hc=$(filter-out h%.c,$(SRC)))

$(info cS=$(filter-out %.c %.S,$(SRC)))

@:;@:

@:;@:

