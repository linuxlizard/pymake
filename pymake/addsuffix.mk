$(info $(addsuffix .c,foo bar))
$(info $(addsuffix .c,foo,bar))

ext=.c
$(info $(addsuffix $(ext),foo bar))

dot=.
c=c
$(info $(addsuffix $(dot)$(c),foo bar))

$(info $(addsuffix c c,foo bar))

@:;@:

