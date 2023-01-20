# creating a space, from the GNU Make manual
blank:= #
space  := ${blank} ${blank}

$(info blank=>>$(blank)<<)
$(info space=>>$(space)<<)

# leading whitespace eaten, intermediate whitesapce preserved,
# trailing whitespace preserved (save output to file to verify)
$(info   5   10    )

$(info 01234567890123456789)
# should see four leading spaces even though $(info) followed by many more
# spaces
$(info       $(subst q,${space},qqqq)<<)

@:;@:

