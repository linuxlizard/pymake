# Tinker with .RECIPEPREFIX
# Note: only supported after Make 3.81
# davep 24-Sep-2014

.RECIPEPREFIX=q

all : ; @echo = all=$@

foo : 
q@echo = foo=$@

