$(info $(words foo bar baz))
$(info $(words      foo       bar 				baz			))
$(info $(words a b c d e f g h i j k l m n o p q r s t u v w x y z))

foo=
$(info $(words $(foo)))

$(info $(words ))

# "Returns the number of words in text. Thus, the last word of text is:"
# -- gnu make manual
text := A B D E F G H I J K L M N O P Q R S T U V W X Y Z _ ! @ $$ % ^ & * ( ) iamlast
$(info $(words $(text)))
$(info $(word $(words $(text)),$(text)))

@:;@:

