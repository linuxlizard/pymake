# How does GNU Make like <tab> inside rule/assignments?
# davep 24-Sep-2014

all	: 	; @echo = all=$@

# assignment - just another whitespace?
abc	def = embedded tab
$(info = embedded tab=$(abc	def))

# not happy in rules; treated as whitepace => separate targets
# The tab\ttab target is warning "target 'tab' given more than once in the same rule"
# Weird! Make only reports this warning if a target explicitly given on cmdline
tabtabtab : tab	tab
tab	tab : ; @echo $@

# whitespace in prereq? or literal <tab>?
# <tab> treated as whitespace
tabtab2 : tab2	tab3
tab2	tab3: ; @echo I am $@

