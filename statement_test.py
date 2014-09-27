def statement_test():
    rules_tests = ( 
        # rule LHS
        ( "all:",    ("all",":")),
        ( "all::",    ("all","::",)),
        # assignment LHS
        ( "all=foo",    ("all","=",)),
        ( "    all  =",    ("all","=")),
        ( "all:=",    ("all",":=",)),
        ( "all::=foo",    ("all","::=",)),
        ( "all?=foo",    ("all","?=",)),
        ( "all+=foo",    ("all","+=",)),
        ( "$(all)+=foo",    ("","$(","all",")","","+=",)),
        ( "qq$(all)+=foo",    ("qq","$(","all",")","","+=",)),
        ( "qq$(all)qq+=foo",    ("qq","$(","all",")","qq","+=",)),

        # kind of ambiguous
        ( "this is a test = ",           ("this is a test","=",) ),
        ( "  this   is   a   test   = ", ("this   is   a   test","=",) ),
        ( "this$(is) $a $test = ",      ("this ","$(","is",")"," ","$","a"," ","$","t","est","=",) ),
        ( "this $(  is  ) $a $test = ",  ("this ","$(","  is  ",")"," ","$","a"," ","$","t","est","=",) ),
        ( "this$(is)$a$(test) : ",       ("this","$(","is",")","","$","a","","$(","test",")","",":",) ),
        ( "this is a test : ",           ("this","is","a","test",":",) ),
        ( "  this   is   a   test   : ", ("this", "is","a","test",":",) ),
        ( "this $(is) $a $test : ",      ("this","$(","is",")","","$","a","","$","t","est","=",) ),

        # yadda yadda yadda
        ( "override all=foo",    ("override","all","=","foo")),

        ( "all:",       ("all",":") ),
        ( "all:foo",    ("all",":","foo")),
        ( "   all :   foo    ", ("all",":","foo")),
        ( "the quick brown fox jumped over lazy dogs : ; ", 
            ("the", "quick", "brown", "fox","jumped","over","lazy","dogs",":", ";", )),
        ( '"foo" : ; ',     ('"foo"',":",";")),
        ('"foo qqq baz" : ;',   ('"foo',"qqq",'baz"',":",";")),
        (r'\foo : ; ',  (r'\foo', ':', ';')),
        (r'foo\  : ; ', (r'foo ',':', ';',)),
        ('@:;@:',       ('@',':',';','@:',)),
        ('I\ have\ spaces : ; @echo $@',    ('I have spaces',':',';','@echo $@',)),
        ('I\ \ \ have\ \ \ three\ \ \ spaces : ; @echo $@', ('I   have   three   spaces',':', ';', '@echo $@' )),
        ('I$(CC)have$(LD)embedded$(OBJ)varref : ; @echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',
            ( 'I', '$(', 'CC', ')', 'have', '$(', 'LD',')','embedded','$(','OBJ',')','varref',':',';',
              '@echo $(subst hello.o,HELLO.O,$(subst ld,LD,$(subst gcc,GCC,$@)))',)
        ),
        ('$(filter %.o,$(files)): %.o: %.c',    
                    ( '', '$(','filter %.o,',
                            '$(','files',')','',
                       ')','',
                          ':','%.o',':','%.c',)),
        ('aa$(filter %.o,bb$(files)cc)dd: %.o: %.c',    
                    ( 'aa', '$(','filter %.o,bb',
                            '$(','files',')','cc',
                       ')','dd',
                          ':','%.o',':','%.c',)),
        ("double-colon1 :: colon2", ("double-colon1","::","colon2")),
        ( "%.tab.c %.tab.h: %.y", ("%.tab.c","%.tab.h",":","%.y")),
        ("foo2:   # hello there; is this comment ignored?",("foo2",":")),
        ("$(shell echo target $$$$) : $(shell echo prereq $$$$)",
            ("","$(","shell echo target $$$$",")","",":","$(shell echo prereq $$$$)",),)
    )
#    for test in rules_tests : 
#        s,result = test
#        my_iter = ScannerIterator(s)
#        tokens = tokenize_assignment_or_rule(my_iter)
#        print( "tokens={0}".format("|".join([t.string for t in tokens])) )

    for test in rules_tests : 
        s,v = test
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_assignment_or_rule(my_iter)
        print( "tokens={0}".format(str(tokens)) )
        print("\n")
#    run_tests_list( rules_tests, tokenize_assignment_or_rule)


