
def split_percent(s):
    # break a string into sub-string before/after a '%'
    # Make sure to check for 
    #   \% (escaped %) 
    #   \\%  (escaped backslash which is a literal %)
    idx = -1
    while 1:
        try:
            idx = s.index('%', idx+1)
        except ValueError:
            return None

        # First check for single \
        # Step1: if we have a char before the % and that char is a \
        # 
        # Next check for double \\  (escaped backslash (literal \) so the % is
        # valid)
        # Step2: if NOT (we have a char before the \ and that char is a \)
        if idx > 0 and s[idx-1] == '\\' and \
      not (idx > 1 and s[idx-2] == '\\'): 
            # at this point we have the case of a backslash'd % so 
            # ignore it, go looking for next possible %
            continue

        # +1 to skip the %
        return s[:idx], s[idx+1:]

def wildcard_match(pattern, strlist):
    p = split_percent(pattern)
    if p is None:
        return [str_==pattern for str_ in strlist]

    return [ str_.startswith(p[0]) and str_.endswith(p[1]) for str_ in strlist ]

def wildcard_replace(search, replace, strlist):
    s = split_percent(search)

    if s is None:
        # no wildcards so just a simple string replace
        return [replace if search==str_ else str_ for str_ in strlist]

    r = split_percent(replace)

    new_list = []
    for str_ in strlist:
        if str_.startswith(s[0]) and str_.endswith(s[1]):
            if r is None:
                new_list.append(replace)
            else:
                mid = str_[len(s[0]) : len(str_)-len(s[1])]
                new = r[0] + mid + r[1]
                new_list.append(new)
        else:
            new_list.append(str_)

    return new_list

new = wildcard_replace("%.c", "%.o", ["foo.c", ".c"])
print(new)

new = wildcard_replace("%.c", "%.o", ["foo.S", "bar.S"])
print(new)

new = wildcard_replace("abc%", "xyz%", ["abcdefg", "abcdqrst",])
print(new)

new = wildcard_replace("abc%", "xyz%123", ["abcdefg", "abcdqrst",])
print(new)

new = wildcard_replace("%", "xyz%123", ["abcdef", "abcdqrst",])
print(new)

# no matches, nothing changed
new = wildcard_replace("foo", "bar", ["abcdef", "tuvwxyz",])
print(new)

# no wildcards
new = wildcard_replace("foo", "bar", ["foo", "bar", "baz"])
print(new)

new = wildcard_replace("f%", "bar", ["foo", "bar", "baz"])
print(new)

# no wildcards in 2nd arg (everything replaced)
new = wildcard_replace("%", "bar", ["foo", "bar", "baz"])
print(new)

