# test the eval function

$(eval FOO:=foo)
$(info a FOO=$(FOO))
$(eval $$(info b FOO=$$(FOO)))

$(eval $$(info hello world 1))

HELLO:=$$(info hello world 2)
$(eval $(HELLO))

FOO:=BAZ:=$$(shell echo baz)
$(eval $(FOO))
$(info BAZ=$(BAZ))

FOO=$(1)=$$(shell echo $(1))

$(info $(call FOO,foo))
$(eval $(call FOO,foo))
$(eval $(call FOO,bar))
$(info foo=$(foo))
$(info bar=$(bar))

define large_comment
    $(info this is a contrived example)
    $(info showing a multi-line variable)
endef

$(eval $(large_comment))

FOO:=FOO error if you see this FOO
BAR:=BAR error if you see this BAR

define silly_example
    FOO:=foo
    BAR:=bar
endef

$(eval $(silly_example))

ifneq ($(FOO),foo)
$(error FOO fail)
endif

ifneq ($(BAR),bar)
$(error BAR fail)
endif

$(info FOO=$(FOO) BAR=$(BAR))

@:;@:

