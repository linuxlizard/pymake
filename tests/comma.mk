# from the GNU make manual
comma:= ,
empty:=
space:= $(empty) $(empty)
foo:= a b c
bar:= $(subst $(space),$(comma),$(foo))

# bar is now ‘a,b,c’.
$(info bar is now $(bar))

@:;@:
