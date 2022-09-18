x=$(dir /etc/passwd)
$(info x=$(x))

x=$(dir /etc/)
$(info /etc/=$(x))

x=$(dir /tmp)
$(info tmp=$(x))

x=$(dir tmp)
$(info tmp=$(x))

@:;@:

