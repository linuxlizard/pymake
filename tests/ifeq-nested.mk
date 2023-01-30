a=10
b=10
#c=10

ifneq "$a" "$b" qqq
    $(info quote a = b)
endif

ifeq ($a,$b)
    $(info a=b)
    ifeq ($b,$c) 
        $(info b=c)
        ifeq ($c,$d   # missing close paren shouldn't be seen
            $(info c=d)
        else
            $(info I am invalid no closing paren
        endif
    else
        $(info b!=c)
    endif
else
    $(info a!=b)
endif

# nest test
ifeq '$(shell date)' '$(shell date)'
    $(info shell is fast)
    ifeq "$(firstword $(shell date))" "Wed"
        $(info It is Wednesday, my dudes.)
    else
        ifeq "$(firstword $(shell date))" "Fri"
            $(info TGIF!)
        else
            ifeq "$(firstword $(shell date))" "Mon"
                $(info I hate Mondays.)
            else
                ifeq "$(firstword $(shell date))" "Sat"
                    $(info Time for yard work)
                else
                    $(info boring day)
                endif
            endif
        endif
    endif
else
    $(info shell is not fast)
endif

@:;@:

