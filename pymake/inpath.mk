# search PATH for a file
# (having fun tinkering with many functions)

define inpath
$(if $(filter $(1),$(notdir $(foreach p,$(subst :, ,$(PATH)),$(wildcard $p/*)))),,$(error $(1) not in path))
endef

ifdef TEST_ME
$(call inpath,gcc)
$(call inpath,arm-marvell-linux-gcc)

endif

