# Experiment with target specific rules.
# GNU Make manual 6.11
# davep 19-Sep-2014

CC=gcc
LD=ld

# avoid the shell from interpretting my test chars
SHELL=/bin/echo

# SHELLFLAGS is feature new in 3.82 (current device running 3.81)
# Previously $(SHELL) lauched with hardcoded -c
#$(info version=$(MAKE_VERSION))
.SHELLFLAGS=

all : normal specific other multiple spaces rules more-spaces confused vbar\
	foovbar whitebar semicolon backslash 2backslash backslash-? \
        2backslash-?

# make -f target-specific.mk normal
normal : 
	@! normal CC=gcc LD=ld!$@ CC=$(CC) LD=$(LD)

# make -f target-specific.mk specific
specific : CC=mycc
specific : LD=myld
specific : 
	@! specific CC=mycc LD=myld!$@ CC=$(CC) LD=$(LD)

# make -f target-specific.mk other
other : CC:=$(CC:gcc=egcs)
other : 
	@! other CC=egcs LD=ld!$@ CC=$(CC) LD=$(LD)

# multiple assignments ; only the first '=' is significant
# this line creates a string $(CC) == intel-cc LD=intel-ld
# make -f target-specific.mk multiple
multiple: CC=intel-cc LD=intel-ld
multiple: 
	@! multiple CC=intel-cc LD=intel-ld LD=ld!$@ CC=$(CC) LD=$(LD)

# double reference 
# make -f target-specific.mk spaces
this is a test=CC
spaces: $(this is a test)=this is a test
spaces:
	@! spaces CC=this is a test LD=ld CC!$@ CC=$(CC) LD=$(LD) $(this is a test)

# Anything after the assignment operator is treated as one token. The CC below creates one big string
# from potato-cc to EOL. CROSS_COMPILE is empty
FOO=BAR
rules: CC=potato-cc LD=potato-ld spaces CROSS_COMPILE=potato $(FOO) potato
rules:
	@! rules CC=@@potato-cc LD=potato-ld spaces CROSS_COMPILE=potato BAR potato@@ LD=@@ld@@ CROSS_COMPILE= TEST=CC!$@ CC=@@$(CC)@@ LD=@@$(LD)@@ CROSS_COMPILE=$(CROSS_COMPILE) TEST=$(this is a test)

# Leading spaces are discarded. Trailing spaces are preserved.
# Comment is successfully ignored.
# make -f target-specific.mk more-spaces
more-spaces :   CC   =   single-trailing-space-cc 
more-spaces :   LD    =     lots-of-trailing-spaces-ld      # I am a comment
more-spaces:
	@% more-spaces CC=@@single-trailing-space-cc @@ LD=@@lots-of-trailing-spaces-ld      @@ TEST=CC%$@ CC=@@$(CC)@@ LD=@@$(LD)@@ TEST=$(this is a test)

# who wins? another ":" indicates an implicit pattern rule. "|" indicates
# order-only prerequisite
# make -f target-specific.mk confused
confused: COLON=:
confused:
	@= :=$(COLON)

# note the single quotes to prevent shell from interpretting the |
# make -f target-specific.mk vbar
vbar: BAR=|
vbar:
	@= |=$(BAR)

# anything before the | cause confusion?
# make -f target-specific.mk foovbar
foovbar: BAR=foo|
foovbar:
	@= foo|=$(BAR)

# whitespaces?
# make -f target-specific.mk whitebar
whitebar: BAR=foo |
whitebar:
	@= foo |=$(BAR)

# So where does semicolon fit in? Normally would terminate the prerequisites.
# The ";" still part of assignment's RHS
semicolon: CC=abcc;echo semicolon > /dev/null
semicolon:
	@= @@abcc;echo semicolon > /dev/null@@=@@$(CC)@@

# Does backspace protect the ";"?  Nope. The \ seems to disappear.
# The target-specific rule's recipe happens after the plain rule's recipe.
# make -f target-specific.mk backslash
backslash: CC=abcdcc\; echo semicolon > /dev/null
backslash:
	@= abcdcc; echo semicolon > /dev/null=$(CC)

# two backslashes protect the semicolon (wha?)
# Note the \ in the recipe protects the ; from the shell.
# make -f target-specific.mk 2backslash
2backslash: CC=abcc\\; echo semicolon
2backslash:
	@= abcc\; echo semicolon=$(CC)

# double trouble- weird char in the target
# make -f target-specific.mk backslash-? 
backslash-? : CC=whocc\?
backslash-? :
	@= whocc\?=$(CC)

# again, the two backspaces translate to a literal \
# make -f target-specific.mk 2backslash-? 
2backslash-? : CC=xyzcc\\?
2backslash-? :
	@= xyzcc\\?=$(CC)


oneline: OCC=gcc; @echo $(CC)
oneline:
	@echo $@ foo foo foo $(OCC)

