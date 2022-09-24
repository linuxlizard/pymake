$(info $(notdir src/foo.c hacks))

x=$(notdir /etc/passwd)
$(info x=$(x))

x=$(notdir /etc/)
$(info /etc/=$(x))

x=$(notdir /tmp)
$(info tmp=$(x))

x=$(notdir tmp)
$(info tmp=$(x))

me=$(PWD)/dir.mk

$(info me=$(me) -> $(notdir $(me)))

me=$(PWD)///////me
$(info me=$(notdir $(me)))

$(info slashy=$(notdir //////tmp//////foo.txt))


@:;@:

