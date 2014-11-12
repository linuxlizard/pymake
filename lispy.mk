# Honestly, car/cdr are close to everything all I know about Lisp. :-/
#
# davep 30-Oct-2014 

define car
$(firstword $(1))
endef

define cdr
$(wordlist 2,$(words $(1)),$(1))
endef

ifdef TEST_ME
list=a b c d e f g 
$(info list=$(list))
$(info car=$(call car,$(list)))
$(info cdr=$(call cdr,$(list)))
$(info cdr=$(call cdr,$(call cdr,$(list))))
$(info cdr=$(call cdr,$(call cdr,$(call cdr,$(list)))))
$(info cdr=$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(list))))))
$(info cdr=$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(list)))))))
$(info cdr=$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(list))))))))
$(info cdr=$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(call cdr,$(list)))))))))

$(info car=$(call car,$(call cdr,$(list))))

lispy_all:;@:
endif

