import itertools

# https://docs.python.org/3/library/itertools.html#itertools.chain.from_iterable
def flatten(list_of_lists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(list_of_lists)

if __name__ == '__main__':
    a = ((6,7),(1,),(2,),(3,),(4,),(5,))
    print(list(flatten(a)))

    a = [["functions*.py"],["*.mk"]]
    print(list(flatten(a)))

