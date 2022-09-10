import itertools

def split_percent(s):
    assert isinstance(s,str), type(s)

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
        return [str_ for str_ in strlist if str_ == pattern]

    return [ str_ for str_ in strlist if str_.startswith(p[0]) and str_.endswith(p[1]) ]

def wildcard_match_list(pattern_list, target_list):
    # pre-calculate all the patterns
    p_list = [split_percent(p) for p in pattern_list]

    print(f"targets={target_list}")

#       value = [t for t in targets if t in filter_on]
    for t in target_list:
        for p,pattern in zip(p_list,pattern_list):
#            print(t,p,pattern)
            if p is None:
                # no '%' so just a string compare
                if t==pattern:
                    yield t
                    break
            elif t.startswith(p[0]) and t.endswith(p[1]):
                yield t
                break


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

filter_on=['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'b', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'b', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
targets=['a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'a', 'b', 'b', 'b', 'b', 'a', 'a', 'a']
5

#x = list(wildcard_match_list(filter_on, targets))
#print(x)


