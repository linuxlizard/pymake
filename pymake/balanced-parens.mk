# GNU Make wants paren/brackets balanced even if not in an actual fn call.
# The open char needs to match the close char ( match ) { match }.
# Opposite char of ( vs { is ignored and can be unbalanced.

a,b = 42
$(info $(a,b),$(a,b))
$(info $$(a,b),$$(a,b))

# literal dollar: parens must balance
$(info $$(()))
${info $${{}}}

# no need to balance (s because using {
${info t=$$(())}
${info t=$$((}

# nested: must balance
${info u=$(info uu=())}

# extra closing ) outside the () but inside {} so ok
${info u=$(info uu=()))}
#                     ^-- extra closing )

# unbalanced opening ( ok because inside {}
${info v=$$(()}

# mismatched open/close
# unterminated call to function 'info': missing ')'
#$(info v=$$(()}

# unterminated call to function 'info': missing ')'
#$(info $$(())

$(info w=$${{{{{)

# balanced { } with ignored ) inside
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

# I don't know why I did this but it's amusing
$(info a$(info b$(info c$(info d$(info e$(info f$info))))))
$(info $$(info $$(info $$(info $$(info $$(info $$info))))))

@:;@:

