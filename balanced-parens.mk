a,b = 42
$(info $(a,b),$(a,b))
$(info $$(a,b),$$(a,b))

# literal dollar
$(info $$(()))

${info t=$$(())}

${info u=$(info uu=())}

${info v=$$(()}

# unterminated call to function 'info': missing ')'
#$(info $$(())

$(info w=$${{{{{)

${info x=$${{{{{)}}}}}}

# unterminated call to function 'info': missing ')'
#$(info $$((((()

# unterminated call to function 'info': missing ')'
#$(info $((((()

# missing separator
#${info foo}}

# missing separator
#${info foo}{

# missing separator
#${info foo}q

$(info $$(info $$(info $$(info $$(info $$(info $$info))))))

@:;@:

