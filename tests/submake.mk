# simple tests of sub-make

all:
	@echo hello from make pid=$$$$
	$(MAKE) -f submake.mk submake A=B B=C C=D
	-$(MAKE) -f submake.mk submake-error

# adding a shell expression to verify we go through the shell
	@$(MAKE) -f submake.mk hello-world NUM=$$((10+20)) a={1,2,3}

submake:
	@echo hello from submake pid=$$$$

hello-world:
	@echo hello, world NUM=$(NUM) a=$(a)

submake-error:
	@echo error && exit 1

