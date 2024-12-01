# Tools in Use

## Github CI

	./.github/workflows/build.yml

Runs tox, codecov. Manually run with

	tox -e py

## Tox

https://tox.wiki/en/latest/installation.html

	tox.ini
just run `tox`    or `tox -e py`

tox.ini also uses pylint, sphinx

## Coverage

https://coverage.readthedocs.io/en/7.3.2/

Triggered by tox. Manually run with:

	coverage run --source=pymake -m pytest -vv
	coverage combine
	coverage report -m

## pytest

https://docs.pytest.org/en/stable/

	# run everything
	PYTHONPATH=. pytest

	# run verbose
	PYTHONPATH=. pytest -v

	# run just the shell tests
	PYTHONPATH=. pytest -k shell

	# run the shell tests with stdout showing
	PYTHONPATH=. pytest -vv -s -k shell

### Test Failures

On failure, pymake and its test code will write the failing test Makefile to 
log/fail.mk  

The test/test_makefile.py runs several test/*.mk files through both GNU Make 
and pymake. The output is compared byte-by-byte. On failure, test/test_makefile.py
will write the output of the both to /tmp with name "makefilename-test.txt" (the pymake 
output) and "makefilename-ground.txt" for the ground truth (the GNU Make output).
For example, foreach.mk-test.txt and foreach.mk-ground.txt will contain the
result of the tests/foreach.mk 


# POSIX

https://pubs.opengroup.org/onlinepubs/9799919799/


# GNU Make Parsing

Closely follow GNU Make's eval() function.  Make doesn't have a formal grammar, 
reserved words, lexical structure. It's an organically grown set of conventions
that have been added to over the years. No formal structure makes it very hard to
parse. The only grammar documentation is the GNU Make source itself.

1. try assignment expressions
2. if not (1) then try conditional line
3. if not (2) then try export/unxport
4. if not (3) then try vpath
5. if not (4) then try include/sinclude/-include
6. if not (5) then try 'load'  (NOT IMPLEMENTED IN PYMAKE)
7. if not (6) then try rule+recipe


# Notes for my future self 

I keep tripping over this problem. Do not use embedded \n in a line fed to
vline. The vline code assumes it receives an array of strings already split by
newlines. The embedded newlines confuse the vline parser.

DO NOT DO THIS!!!
    "SRC\\\n=\\\nhello.c\\\n\n",
do this instead:
    "SRC\\\n", "=\\\n", "hello.c\\\n", "\n"

