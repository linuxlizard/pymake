pymake
======

Parse GNU Makefiles with Python

I want to debug my GNU Makefiles.

Ultimate long-term goal is a GNU Make visual debugger. I want breakpoints on variables changing. I want to single step through the rules. I want to put a breakpoint on a rule.

## Update 20231018.  The Lawyer Update.

I've been asked by my employer to suspend work on this project because it is GPL licensed. I'm asking for further clarification but will need to wait for a while.

## Update 20230704. The Dragon Isles Update.

Today I am declaring my Independence Day from from a certain game and reclaiming my spare time. My next short-term goal for pymake is to be able to build GNU Make.


## Update 20230412. The "What am I Doing" Update.

Had a bit of a break due to my finding [remake](https://remake.readthedocs.io/en/latest). The remake tool is a fork of GNU Make which adds interactive command line debugging to Make.  Sound familiar?  Remake did not exist when I started on my little PyMake adventure.  I started wondering if I should continue my little project.  I took a few weeks to play with Rust (really cool language).  Then I decided I want to finish this project. I love working with programming languages. My thesis was a mini-Ada compiler. So, anyway, let's get this thing working.


## Update 20230208. The Covid Update.

Away from work sick with Covid. Not sick enough to not be bored watching TV. 
* include directives work (need more testing)
* starting multi-line 'define' variables
* revamped the tokenizer to better handle rules vs expressions
* because of the improved tokenizer, much improved conditional block handling

## Update 20230122. More Pythonic.

Thanks to a PR, the code is in a much cleaner, more Pythonic state. All the test code and test makefiles are now in tests/ directory. 

I've been battling problems with recipeprefix (aka 'tab').  GNU Make's parser is a bit ad-hoc and I need to match their behavior. Correctly supporting the is-a-recipe / is-not-a-recipe on lines starting with 'tab' is going to require a refactor of the tokenizer.

## Update 20221224. Large Updates.

I have rules started. I have conditional directives working (needs more
testing).  The export and unexport directives work.  I've been adding as many
new pytest tests as I can think of.

Still TODO: 
* include directives 
* override directive
* 'define' multi-line variable definitions.

## Update 20220924. Array of Strings vs Space Separated Strings.

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

     python -m pymake.pymake -f Makefile

Parse/execute functions.mk, rewrite the makefile from the parsed source to out.mk (very useful for seeing a cleaned makefile)

    python -m pymake.pymake -o out.mk -f Makefile
