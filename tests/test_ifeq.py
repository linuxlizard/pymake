import pytest

import run

def test_nested_missing_endif():
    s = """
ifeq (10,10)
    ifeq (a,b)
        
endif
@:;@:
"""
    msg = run.pymake_should_fail(s)
    assert "missing endif" in msg
    
def test_nested_skipped_missing_endif():
    s = """
ifeq (10,11)
    ifeq (a,b
        
endif
@:;@:
"""
    msg = run.pymake_should_fail(s)
    assert "missing endif" in msg

def test_nested():
    s = """
ifeq (10,10)
    ifeq (a,b)
    endif        
endif
@:;@:
"""
    run.pymake_string(s)

def test_deep_nested():
    s = """
ifeq (10,10)
    ifeq (11,11)
        ifeq (12,12)
            ifeq (13,13)
                ifeq (14,14)
                    ifeq (15,15)
                        ifeq (16,16)
                            ifeq (17,17)
                                ifeq (18,18)
                                    ifeq (19,19)
                                        ifeq (20,20)
                                        $(info 20)
                                        endif
                                    $(info 19)
                                    endif
                                endif
                            endif
                        endif
                    endif
                endif
            endif
        endif
    endif        
endif
@:;@:
"""
    run.pymake_string(s)

def test_deep_nested_else():
    s = """
ifeq (10,10)
    ifeq (11,11)
        ifeq (12,12)
            ifeq (13,13)
                ifeq (14,14)
                    ifeq (15,15)
                        ifeq (16,16)
                            ifeq (17,17)
                                ifeq (18,18)
                                    ifeq (19,19)
                                        ifeq (20,20)
                                        else
                                        endif
                                    else
                                    endif
                                else
                                endif
                            else
                            endif
                        else
                        endif
                    else
                    endif
                else
                endif
            else
            endif
        else
        endif
    else
    endif        
else
endif
@:;@:
"""
    run.pymake_string(s)

def test_nested_valid_inside():
    s = """
ifeq (10,10)
    ifeq (a,a)
        $(info should see this)
    endif
endif
@:;@:
"""
    run.pymake_string(s)
    
def test_nested_invalid_inside():
    # note the missing close ) on the inner expression
    s = """
ifeq (10,11)
    ifeq (a,a
        $(error should not see this)
    endif
endif
@:;@:
"""
    run.pymake_string(s)

def test_bare_endif():
    s = """
endif
@:;@:
"""
    msg = run.pymake_should_fail(s)
    assert "extraneous 'endif'" in msg

# This is a weird corner case. Check for a directive that isn't
# properly whitespace separated. GNU Make doesn't detect it as
# a directive in conditional_line()-src/read.c so it falls
# through to the catch-all error "missing separator". My parser
# is dependent on whitespace so an improper directive will be
# ignored until execute() stage.
# ifeq'1' '1'  <-- note missing whitespace after ifeq
# endif
@pytest.mark.skip(reason="FIXME missing whitespace after ifeq")
def test_missing_whitespace_ifeq():
    s = """
ifeq(a,b)
endif
@:;@:
"""
    msg = run.pymake_should_fail(s)
    assert "missing endif" in msg

def test_bare_ifdef():
    s = """
ifeq
@:;@:
"""
    msg = run.pymake_should_fail(s)
    assert "invalid syntax in conditional" in msg

def test_bare_ifdef_whitespace():
    # NOTE!  there are trailing whitespace after the ifdef
    s = """
ifeq    
@:;@:
"""
    msg = run.pymake_should_fail(s)
    assert "invalid syntax in conditional" in msg

