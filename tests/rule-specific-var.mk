# Can I have rule specific assignments and recipes together?
# NOPE.
# 
# The "foo : FOO=BAR ; @echo bar bar bar" creates a variable 
# $(FOO)=="bar ; @echo bar bar bar"
#
# Verified 3.81 3.82 4.0

abc : xyz ; def

         #vvvvvvvvvvvvvvvvvvvvvvv--------  part of $(FOO)
foo : FOO=BAR ; echo oof oof oof
#foo : ; @echo foo foo foo $(FOO)
foo : \
; @echo \
foo \
foo \
foo \
$(FOO)

# cmd launched: echo foo foo foo ; echo oof oof off

bar : BAR=FOO  # hello I am a comment
bar :  # hello I am another comment
	@echo bar bar bar $(BAR)

baz : BAZ\
=\
BAR
baz : 
	@echo baz baz baz $(BAZ)

