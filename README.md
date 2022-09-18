pymake
======

Parse GNU Makefiles with Python

I want to debug my GNU Makefiles.

Ultimate long-term goal is a GNU Make visual debugger. I want breakpoints on variables changing. I want to single step through the rules. I want to put a breakpoint on a rule.

## Update 20220917. Whitespace Whitespace Whitespace.

Whitespace is incredibly finicky in GNU Make.  I have almost all of the string functions implemented but I keep running into strange whitespace problems.

## Update 202208017.  Welcome to PyMake. 

Hello! Welcome! Someone noticed my silly little project.

My goal is a source level debugger for GNU Makefiles. (Nothing against other Make implementations but I have to start somewhere.) The plan is to have a text interface like gdb.

The project is very early. I can parse almost all of fully formed makefiles.  I can output S-expressions, regenerate the makefile. 

As of this writing, I am implementing the GNU make $() functions. I cannot yet execute rules so I'm not yet actually a fully functioning Make.

### Example usage:


Read a makefile, dumps incredible amounts of debugging while parsing. Output of the makefile got to stdout

    python3 pymake.py Makefile

Parse/execute functions.mk, rewrite the makefile from the parsed source to out.mk (very useful for seeing a cleaned makefile)

    python3 pymake.py -o out.mk functions.mk

