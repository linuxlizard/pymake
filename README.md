pymake
======

Parse GNU Makefiles with Python

I want to debug my GNU Makefiles.

Ultimate long-term goal is a GNU Make visual debugger. I want breakpoints on variables changing. I want to single step through the rules. I want to put a breakpoint on a rule.

## Update 20221224. Large Updates.

I have rules started. I have conditional directives working (needs more
testing).  The export and unexport directives work.  I've been adding as many
new pytest tests as I can think of.

Still TODO: 
* include directives 
* override directive
* 'define' multi-line variable definitions.

## Update 20220924. Throwing in the Towel.

My original plan of returning arrays of python strings in the $() functions has
been scrapped. I'm now building a 100% python string from each function. The
functions .eval() will return a python string with the proper whitespacing. A
chained function will be responsible to split() a string again to find the
fields. There were just too many strange corner cases.

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

