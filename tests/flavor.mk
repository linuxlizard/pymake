# env vars show up as recursive? weird.
$(info PATH=$(flavor PATH))
$(info TERM=$(flavor TERM))

a=a
$(info a=$(flavor a))

b:=b
$(info b=$(flavor b))

# undefined (treated as 'a b')
$(info a b=$(flavor a b))

# whitespace is collapsed
$(info a    b =$(flavor   a   b   ))

@:;@:

