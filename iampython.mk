
SHELL="/bin/echo"

if sys.version_info.major < 3:
	raise Exception("Requires Python 3.x")

#% : ; @echo {implicit} $@

