#!/usr/bin/env python

import sys
import itertools
import pprint

class TODO(Exception):
    pass

def stringify(arg):
    if isinstance(arg,list):
        # only allow one level deep 
        return " ".join([str(a) for a in arg])
    return str(arg)

class Value(object):
    def __init__(self,args):
        print("Value={0} args={1}".format(repr(self),repr(args)))
        if not args : 
            self.value = []
        else : 
            if isinstance(args,list):
                # only allow one level deep
                for v in args: 
                    assert isinstance(v,Atom),(type(v),v)
                # make a copy
                self.value = list(args)
            elif isinstance(args,Value) : 
                # "copy constructor"; create a new Value from an existing Value
                self.value = list(args.value)
            else : 
                assert isinstance(args,Atom),(type(args),args)
                self.value = [args]

    def execute(self):
        # return a new instance of my own value
        v = Value(self.value)
        print("Value={0}.execute() value={1} v={2}".format(
                repr(self),repr(self.value),repr(v)))
        return v
        
    def __str__(self):
#        print("Value={0}.__str__() value={1} value={2}".format(
#                repr(self),repr(self.value),stringify(self.value)))

        def tostr(value):
            if isinstance(value,list):
                # only allow one array level deep 
                for v in value : 
                    assert isinstance(v,Atom),(type(v),)
                return "".join( [ str(v) for v in value ] )
            return str(value)

        return tostr(self.value)

    def __iter__(self):
        return iter(self.value)

    @staticmethod
    def flatten(value_list):
        # construct a single Value() from an array of Value()
        print( "Value.flatten() value_list={0}".format(value_list))
        Value.sanity(value_list)

        # https://stackoverflow.com/questions/406121/flattening-a-shallow-list-in-python
        return Value(list(itertools.chain.from_iterable(value_list)))
    
    @staticmethod
    def sanity(value_list):
        assert isinstance(value_list,list),(type(value_list),)
        for v in value_list :
            assert isinstance(v,Value),(type(v),)

class SymbolTable(object):
    def __init__(self):
        # Array of hashes. Each hash is a scope.
        self.table = [ {} ]

        self.pp = pprint.PrettyPrinter(indent=4)

    def pprint(self):
        print( "pprint symtable=", end="" )
        self.pp.pprint(self.table)

    def push(self):
        # push a scope
        self.table.append( {} )

    def pop(self):
        # pop a scope
        self.table.pop()

    def set(self,name,value=None):
        # if the name exists, update its value
        # if the name doesn't exist, created it in the current scope
        if value is None : 
            value = []
        Value.sanity(value)

        print( "symtable.set({0}) value={1}".format(name,repr(value)))

        symbol = self.table[-1].get(name,None)
        self.table[-1][name] = value
        
    def get(self,name):
        # return the node for this name
        #
        # TODO search backwards up the scopes
        value = self.table[-1].get(name,None)
        print( "symtable.get({0}) value={1}".format(name,repr(value)))
        return value

    def __str__(self):
        currscope = self.table[-1]
        def tostr(value):
            if isinstance(value,list):
                return " ".join( [ tostr(v) for v in value ] )
            assert isinstance(value,Value),(type(value),)
            return str(value)

        s = "\n".join( [ "{0}={1}".format(k, tostr(currscope[k])) \
                            for k,v in currscope.items() ] )
        return s

symtable = SymbolTable()

class Atom(object):
    def __init__(self,value):
        self.value = value
        print("Atom={0} value={1}".format(repr(self), self.value))

    def execute(self):
        print("Atom={0}.execute() value={1}".format(
                repr(self), self.value))
#        return self
        return [ Value(self) ]

    def __str__(self):
        return str(self.value)

class Ref(object):
    def __init__(self,name):
        print("Ref={0} name={1}".format(repr(self),name))
        self.name = name

    def execute(self):
        print("Ref={0}.execute() name={1}".format(repr(self),self.name))
        value = symtable.get(self.name)
        assert isinstance(value,list),(type(value),)
        assert len(value)
        print(value[0])
        if value is None : 
            raise TODO()
            return Value()

        print("Ref={0}.execute() value={1}".format(repr(self),repr(value)))

        for v in value:
            assert isinstance(v,Value),(type(v),)
            print("v={0} {1}".format(v,type(v)))

        # return copy of the value(s) from the symbol table
        if isinstance(value,list):
            return [ Value(v) for v in value ]

        assert 0
        raise TODO()
        return Value(value)

    def __str__(self):
        raise TODO()

class Expr(object):
    def __init__(self,*args):
        print("Expr={0} args={1}".format(repr(self),args))
        self.args = list(args)

    def execute(self):
        print("Expr={0}.execute()".format(repr(self)))
        values = []
        for v in self.args : 
            print("Expr={0}.execute() type(v)={1}".format(repr(self),type(v)))
            e = v.execute()
            Value.sanity(e)
#            assert isinstance(e,list),(type(e),)
#            for eprime in e : 
#                assert isinstance(eprime,Value),(type(eprime),)
            values.extend(e)

#        return Value( [ a.execute() for a in self.args ] )
        return values

    def __str__(self):
        raise TODO()

class Assign(object):
    def __init__(self,dst,*srcargs):
        print("Assign={0} dst={1} srcargs={2}".format(
                repr(self),repr(dst),repr(srcargs)))
        assert isinstance(dst,Expr)
        self.dst = dst

        if not srcargs : 
            # empty RHS
            self.src = Value()
        else : 
            for s in srcargs : 
                assert isinstance(s,Expr),(type(s),)
            self.src = list(srcargs)

    def execute(self):
        print("Assign={0}.execute()".format(repr(self)))
        dstvalue = self.dst.execute()
        # dstvalue must be an rray of value
        Value.sanity(dstvalue)
        # convert array of value to a string
        dstname = stringify(dstvalue)

        # self.src is array of Expr
        # All .execute() methods return array of Value
        # so Expr.execute() returns array of Value
        # so s.execute() returns array of Value 
        # so would normally get array of array of value [ [Value(),...], ... ]
        # Need to flatten the inner array of Value into a single Value
        srcvalue = [ s.execute() for s in self.src ]

#        srcvalue = [ Value.flatten(s.execute()) for s in self.src ]

        Value.sanity(srcvalue)

        symtable.set(dstname,srcvalue)

    def __str__(self):
        raise TODO()

def main() : 
#    a = Atom("a")
#    print("a={0}".format(a))
#    a1 = a.execute()
#    print("a1={0} {1}".format(repr(a1),a1))
#    assert id(a)==id(a1)
#    e = Expr(a)
#    e_out = e.execute()

    v1 = Value(Atom("x"))
    print("v1={0}".format(v1))
    v2 = Value( [ Atom("a"), Atom("b"), Atom("c") ] )
    print("v2={0}".format(v2))
    v3 = Value.flatten( [ v1, v2 ] )
    print("v3={0}".format(v3))
#    return 

    print( "a = 10")
    a1 = Assign( Expr(Atom("a")), Expr(Atom("10")) )
    a1.execute()
    symtable.pprint()
    print(symtable)
    print(repr(symtable.table[-1]))

    ref = Ref("a")
    e = ref.execute()
    print("Ref(a).execute()={0}".format(e))

    e = Expr(Ref("a"))
    e_out = e.execute()

    print("b = $a")
    a2 = Assign( Expr(Atom("b")), Expr(Ref("a")) )
    a2.execute()
    print(symtable)

    # no spaces -> one expression
    print("c = $b$b")
    a3 = Assign( Expr(Atom("c")), Expr(Ref("b"),Ref("b")) )
    a3.execute()
    print(symtable)
    
    # embedded spaces -> two expressions
    print( "d = 10 10")
    a4 = Assign( Expr(Atom("d")), Expr(Atom("10")),Expr(Atom("10")) )
    a4.execute()
    print(symtable)

    print( "e = 1010" )
    a5 = Assign( Expr(Atom("e")), Expr(Atom("10"),Atom("10")) )
    a5.execute()
    print(symtable)

    print("f = $a $a")
    a6 = Assign( Expr(Atom("f")), Expr(Ref("a")),Expr(Ref("a")) )
    a6.execute()
    print(symtable)

    print("g=$f")
    a7 = Assign( Expr(Atom("g")), Expr(Ref("f")) )
    a7.execute()
#    print(symtable)
    g = symtable.get("g")
    print(g)
    print(g[0])

    print("\n\n\n")
    symtable.pprint()
    f = symtable.get("f")
    c = symtable.get("c")
    print("f={0}".format(f))
    print("f={0}".format(stringify(f)))
    print("c={0}".format(c))
    print("c={0}".format(stringify(c)))

    validate = {
        "a" : "10",
        "b" : "10",
        "c" : "1010",
        "d" : "10 10",
        "e" : "1010",
        "f" : "10 10",
        "g" : "10 10",
    }
    print("all symbols:")
    scope = symtable.table[0]
    for k,v in scope.items():
        s = stringify(v)
        print("{0}={1}".format(k,s))
    for k,v in scope.items():
        s = stringify(v)
        assert validate[k]==s, (k,s,validate[k])

if __name__=='__main__':
    main()

