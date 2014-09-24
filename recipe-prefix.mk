# Tinker with .RECIPEPREFIX
# davep 24-Sep-2014

.RECIPEPREFIX=q

all : ; @echo = all=$@

foo : 
q@echo = foo=$@

