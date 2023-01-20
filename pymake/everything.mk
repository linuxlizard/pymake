# (almost) all Make features in one file
#
# davep 4-Dec-204

FOO=foo
BAR:=bar
BAZ+=baz
XYZZY?=xyzzy
#NULL ::=null
#BSOD!=bsod

vpath %.c src

export RTFM=WTF
export id10t=davep
export 
export FOO BAR BAZ XYZZY

unexport RTFM
unexport BAR BAZ

# pymake doesn't support yet
#define range
#$(if $(word $(1),$(2)),$(2),$(call range,$(1),$(2) $(words $(2))))
#endef

a=$(FOO)$(BAR)$(BAZ)
b=$(FOO) $(BAR) $(BAZ)
deadbeef := dead$(XYZZY)beef
deadbeef := dead$(XYZZY)beef

# if/else/else/else/endif
count?=3
ifeq ($(count),1)
    $(info Thou count to three, no more, no less.)
else ifeq ($(count),2)
    $(info Neither count thou two, excepting that thou then proceed to three.)
else ifeq ($(count),3)
    $(info Lobbest thou thy Holy Hand Grenade of Antioch towards thy foe,\
    who being naughty in My sight, shall snuff it.)  # amen
else ifeq ($(count),4)
    $(info Four shalt thou not count.)
else ifeq ($(count),5)
    # three, sir!
    $(info Five is right out.)
else
    $(error blew thyself up)
endif

all : or nothing
	@echo all
        
# target specific variable
foo : FOO=more foo!
foo :
	@echo $(FOO)

bar baz xyzzy : foo 
	@echo $@
	@echo $<
	@echo $?

# pymake can't parse yet
# order only prerequisite
#bsod : windows | msdos

# pymake can't parse yet
# static pattern rule
#gigo : garbage-in : garbage-out

sometimes=y
vowels=a e i o u $(sometimes)
alphabet = a b c d e f g h i j k l m n o p q r s t u v w x y z
consonants = $(filter-out $(vowels),$(alphabet))
$(info $(consonants))
soup : $(alphabet) 0 1 2 3 4 5 6 7 9
internet_startup : $(consonants) 

# double colon rule
USER=davep
pebkac :: $(USER)chair 
pebkac :: problem
pebkac :: $(USER)keyboard

xon : xoff
xoff: xon

include smallest.mk
sinclude notexist.mk
-include notexist.mk

% : ; @echo {implicit} $@

