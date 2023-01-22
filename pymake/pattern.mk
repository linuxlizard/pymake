SRC=hello.c there.c all.c you.c rabbits.c
OBJ=$(patsubst %.c,%.o,$(SRC))

$(info OBJ=$(OBJ))

$(info emptyc=$(patsubst %.c,%.o,.c .o))

$(info .S=$(patsubst %.c,%.o,$(patsubst %.c,%.S,$(SRC))))
$(info .h=$(patsubst %.S,%.h,$(patsubst %.c,%.o,$(patsubst %.c,%.S,$(SRC)))))

$(info h=$(patsubst h%.c,%.o,$(SRC)))
$(info hq=$(patsubst h%.c,q%.o,$(SRC)))
$(info qh=$(patsubst h%.c,%q.o,$(SRC)))

$(info hqq=$(patsubst %o.c,h%q.o,$(SRC)))

$(info $(patsubst he%.c,h%.h,$(SRC)))

# nothing should change (no wildcards)
$(info $(patsubst c,h,$(SRC)))

# whole string substitution
$(info $(patsubst foo,bar,foo bar baz))
$(info $(patsubst foo,bar%,foo bar baz))

$(info $(patsubst %,bar,foo bar baz))
$(info $(patsubst f%,bar,foo bar baz))

$(info $(patsubst %,xyz%123,abcdef abcdqrst))
@:;@:
