x=$(realpath /etc/passwd)
$(info x=$(x))

x=$(realpath /lib)
$(info x=$(x))

x=$(realpath /lib /etc/passwd /tmp)
$(info x=$(x))

# does not exist -> empty
$(info dave=$(realpath /etc/dave))

$(info $(realpath ../))
$(info $(realpath ../../))

# this is not portable across tests (pid will be different)
#$(info $(realpath /proc/self))

$(info $(realpath /lib /lib32 /lib64 /bin))

$(info $(realpath $(sort $(wildcard /lib/*.so))))

@:;@:

