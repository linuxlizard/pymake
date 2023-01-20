$(info $(addprefix src/,foo bar))

$(info $(addprefix src/,foo,bar))

# TODO *** insufficient number of arguments (1) to function 'addprefix'.  Stop.
#$(info $(addprefix src/))

$(info $(addsuffix .c,$(addprefix src/,foo bar)))

$(info $(addprefix $(HOME)/build/,$(addsuffix .c,$(addprefix src/,foo bar))))

$(info $(addprefix c c,foo bar))

@:;@:


