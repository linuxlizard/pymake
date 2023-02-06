
hello: hello.o

hello.o: CFLAGS+=-DWORLD="\"WoRlD\""
hello.o: hello.c hello.h

clean: ; $(RM) hello hello.o
