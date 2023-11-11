# simple tests of sub-make

$(info CURDIR=$(CURDIR))

# check on MAKELEVEL value
$(if $(MAKELEVEL),,$(error MAKELEVEL is missing))

all:
	@echo hello from make pid=$$$$
	$(MAKE) -f $(CURDIR)/tests/submake.mk submake A=B B=C C=D

# we should ignore this error and continue
	-$(MAKE) -f $(CURDIR)/tests/submake.mk submake-error

# adding a shell expression to verify we go through the shell
	@$(MAKE) -f $(CURDIR)/tests/submake.mk hello-world NUM=$$((10+20)) a={1,2,3}

	if [ -z '$(MAKELEVEL)' ] ; then echo missing MAKELEVEL && exit 1 ; fi
	if [ ! $(MAKELEVEL) -eq 0 ] ; then echo MAKELEVEL should be zero && exit 1 ; fi

submake:
	@echo hello from submake pid=$$$$
	if [ ! $(MAKELEVEL) -eq 1 ] ; then echo MAKELEVEL should be value 1 && exit 1 ; fi

hello-world:
	if [ ! $(MAKELEVEL) -eq 1 ] ; then echo MAKELEVEL should be value 1 && exit 1 ; fi
	@echo hello, world NUM=$(NUM) a=$(a)

submake-error:
	if [ ! $(MAKELEVEL) -eq 1 ] ; then echo MAKELEVEL should be value 1 && exit 1 ; fi
	@echo error && exit 1

