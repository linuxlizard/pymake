from wildcard import split_percent, wildcard_match, wildcard_replace

def test_split():
    p = split_percent("hello.c")
    print(p)
    assert p is None

    p = split_percent("%.c")
    print(p)
    assert p and p[0] == '' and p[1] == '.c'

    p = split_percent("hello.%")
    print(p)
    assert p and p[0]=='hello.' and p[1] == ''

    p = split_percent("hello%.c")
    print(p)
    assert p and p[0]=='hello' and p[1] == '.c'

    p = split_percent("hello\\%.c")
    print(p)
    assert p is None

    # the \\\\ becomes \\ becomes a literal backslash
    p = split_percent("hello\\\\%.c")
    print(p)
    assert p and p[0]=='hello\\\\' and p[1]=='.c'

    p = split_percent("hello\\%there%.c")
    print(p)
    assert p and p[0]=='hello\\%there' and p[1]=='.c'

    p = split_percent("hello\\%there%.c")
    print(p)
    assert p and p[0]=='hello\\%there' and p[1]=='.c'

    p = split_percent("hello\\\\%")
    print(p)
    assert p and p[0]=='hello\\\\' and p[1]==''

    p = split_percent("\\\\%")
    print(p)
    assert p and p[0]=='\\\\' and p[1]==''

    # ignore 2nd %
    p = split_percent("\\\\%%.c")
    print(p)
    assert p and p[0]=='\\\\' and p[1]=='%.c'

    # literal % (no % to split around)
    p = split_percent("\\%")
    print(p)
    assert p is None
#    assert p and p[0]=='\\%' and p[1]==''

    # literal % followed by wildcard %
    p = split_percent("\\%%.c")
    print(p)
    assert p and p[0]=='\\%' and p[1] == '.c'

def test_match():
    matches = wildcard_match("hello.c", ("hello.c",))
    assert matches and matches == ["hello.c"]

    matches = wildcard_match("hello.c", ("there.c",))
    assert len(matches)==0

    matches = wildcard_match("%.c", ("hello.c",))
    assert matches and matches == ["hello.c"]

    matches = wildcard_match("hello.c", ("hello.c", "there.c", "all.c", "you.c", "rabbits.c"))
    assert matches and matches == ["hello.c"]

    matches = wildcard_match("%.c", ("hello.c", "there.c", "all.c", "you.c", "rabbits.c"))
    assert matches == ["hello.c", "there.c", "all.c", "you.c", "rabbits.c"]

    matches = wildcard_match("hello.%", ("hello.c", "there.c", "all.c", "you.c", "rabbits.c"))
    assert matches == ["hello.c"]

#    flag = wildcard_match("hello.c", "%.c")
#    assert flag

def test_replace():
    filenames = wildcard_replace("%.c", "%.o", ("hello.c",))
    assert filenames[0]=="hello.o"

    # weird ; no basename
    new = wildcard_replace("%.c", "%.o", ["foo.c", ".c"])
    print(new)
    assert new==["foo.o", ".o"]

    # nothing should change
    new = wildcard_replace("%.c", "%.o", ["foo.S", "bar.S"])
    print(new)
    assert new == ["foo.S", "bar.S"]

    new = wildcard_replace("abc%", "xyz%", ["abcdefg", "abcdqrst",])
    print(new)
    assert new == ["xyzdefg", "xyzdqrst"]

    new = wildcard_replace("abc%", "xyz%123", ["abcdefg", "abcdqrst",])
    print(new)
    assert new == ["xyzdefg123", "xyzdqrst123"]

    new = wildcard_replace("%", "xyz%123", ["abcdef", "abcdqrst",])
    print(new)
    assert new == ["xyzabcdef123", "xyzabcdqrst123"]

    # no matches, nothing changed
#    new = wildcard_replace("foo", "bar", ["abcdef", "tuvwxyz",])
#    print(new)
#    assert new == ["abcdef", "tuvwxyz"]

    # no wildcards
#    new = wildcard_replace("foo", "bar", ["foo", "bar", "baz"])
#    print(new)
#    assert new == ["bar", "bar", "baz"]

#    new = wildcard_replace("f%", "bar", ["foo", "bar", "baz"])
#    print(new)
#    assert new == ["bar", "bar", "baz"]

    # no wildcards in 2nd arg (everything replaced)
#    new = wildcard_replace("%", "bar", ["foo", "bar", "baz"])
#    print(new)
#    assert new == ["bar", "bar", "bar"]

if __name__ == '__main__':
#    test_split()
    test_match()
    
