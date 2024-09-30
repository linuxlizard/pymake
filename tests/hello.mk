# this is a comment

CC=gcc
CFLAGS=-g -Wall

EXE=hello
OBJ=hello.o

FOO:=bar

all: $(EXE)
# should see FOO=BAZ (assigned at bottom of file) because all the file is
# parsed/run before rules are executed
	echo FOO=${FOO}

hello : hello.o
	$(CC) $(CFLAGS) -o $@ $^

hello.o : hello.c
	$(CC) $(CFLAGS) -c -o $@ $^

clean : ; $(RM) $(OBJ) $(EXE)

$(info RM=$(RM))

# make parses/runs whole file before starting on the rules
# (will see this message before rules are run)
$(info end of file bye now come again)

FOO:=BAZ

