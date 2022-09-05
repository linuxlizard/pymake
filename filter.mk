# davep 20220902 ; let's figure out how GNU Make's filter() sees the world.

x:=a a a a a a a a a a a b

$(info   5   x=$(filter   $(strip $(x)) $(x) $(shell seq 1 10) a   b   c   d   e   f   g   h   i   j   k   l   m   n   o   p   q   r   s   t   u   v   w   x   y   z,$(x)   b   b   b   a   a   a))
$(info 5 x=$(filter a b c d e f g h i j k l m n o p q r s t u v w x y z,$(x) b b b a a a))
$(info 1 x=$(filter a,$(x)))
$(info 2 x=$(filter a,$(x) b b b ))
$(info 3 x=$(filter a,$(x) b b b a a a))
$(info 4 x=$(filter a b,$(x) b b b a a a))
$(info 5 x=$(filter a b c d e f g h i j k l m n o p q r s t u v w x y z,$(x) b b b a a a))

a:=a
$(info 6 x=$(filter $(a),$(x)))
b:=b
$(info 7 x=$(filter $(a) $(b),$(x)))

$(info 8 x=$(filter $(a)$(b),$(x)b $(x)b))

$(info 9 x=$(filter $(a), a))
$(info a x=$(filter a,a,a,a,a,a))

acomma=a,a
$(info acomma x=$(filter $(acomma),a,a,a,a,a))
$(info acomma x=$(filter $(acomma),a,a a,a a))
$(info acomma x=$(filter a $(acomma),a,a a,a a))

# confusing but I think Make is seeing this
# as filter "a" in ("a", ",", "a", ",", ... "a")
$(info x=>>$(filter a, a , a , a , a , a)<<)

comma=,
$(info comma x=$(filter $(comma),a,a,a,a,a))
$(info comma x=$(filter $(comma),a , a , a , a , a))

x=       a    b   c    d    e   f    g 
$(info spaces x=$(filter a b,$x))
$(info spaces x=$(filter              a      b     ,     $x      ))
$(info spaces x=$(filter              a      b   $(comma)  ,     $x    $(comma) $(comma) ))


@:;@:

