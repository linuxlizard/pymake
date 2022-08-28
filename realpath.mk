x=$(realpath /etc/passwd)
$(info x=$(x))

x=$(realpath /lib)
$(info x=$(x))

x=$(realpath /lib /etc/passwd /tmp)
$(info x=$(x))

@:;@:

