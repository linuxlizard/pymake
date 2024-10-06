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


