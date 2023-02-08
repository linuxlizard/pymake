hello: hello.o

# verify an expression handled correctly in a prereq
hello.o: $(foreach s,c h,hello.$s)

clean: ; $(RM) hello hello.o

