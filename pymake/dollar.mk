# in make, a $$ -> literal $
#
a=q

@: q
	echo $ a

$(a) : 
	echo a=$a
	b=$a && echo $$$$
	b=$$a a=10 && echo da=$a dda=$$a ddda=$$$a dddda=$$$$a dddddda=$$$$$$$a ddddddda=$$$$$$$a 

