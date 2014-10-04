# this is a comment

CC=gcc
CFLAGS=-g -Wall

EXE=hello
OBJ=hello.o

all: $(EXE)

hello : hello.o
	$(CC) $(CFLAGS) -o $@ $^

hello.o : hello.c
	$(CC) $(CFLAGS) -c -o $@ $^

clean : ; $(RM) $(OBJ) $(EXE)

