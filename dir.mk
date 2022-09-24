$(info $(dir src/foo.c hacks))

x=$(dir /etc/passwd)
$(info x=$(x))

x=$(dir /etc/)
$(info /etc/=$(x))

x=$(dir /tmp)
$(info tmp=$(x))

x=$(dir tmp)
$(info tmp=$(x))

me=$(PWD)/dir.mk

$(info me=$(me) -> $(dir $(me)))

me=$(PWD)///////me
$(info me=$(dir $(me)))

$(info slashy=$(dir //////tmp//////foo.txt))

@:;@:

