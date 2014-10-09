FOO=bar
ifdef FOO
$(info $(FOO))
else
$(error need foo )
endif

all:;@:

