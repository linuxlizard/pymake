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
    flags = wildcard_match("hello.c", ("hello.c",))
    assert all(flags)

    flags = wildcard_match("hello.c", ("there.c",))
    assert not all(flags)

    flags = wildcard_match("%.c", ("hello.c",))
    assert all(flags)

    flags = wildcard_match("hello.c", ("hello.c", "there.c", "all.c", "you.c", "rabbits.c"))
    assert flags[0]
    assert not(all(flags[1:]))

    flags = wildcard_match("%.c", ("hello.c", "there.c", "all.c", "you.c", "rabbits.c"))
    assert all(flags)

    flags = wildcard_match("hello.%", ("hello.c", "there.c", "all.c", "you.c", "rabbits.c"))
    assert flags[0]
    assert not(all(flags[1:]))

#    flag = wildcard_match("hello.c", "%.c")
#    assert flag

def test_replace():
    filenames = wildcard_replace("%.c", "%.o", ("hello.c",))
#    assert filenames[0]=="hello.o"

    filenames = wildcard_replace("h%.c", "h%.o", ("hello.c","there.c"))
