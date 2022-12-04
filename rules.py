#!/usr/bin/env python3

import logging

logger = logging.getLogger("pymake.rules")

from error import *

_debug = True

class Rule:
    def __init__(self, target, prereq_list, recipe_list):
        # ha ha type checking;  must quack like a symbol.RecipeList
        [r.recipe for r in recipe_list]

        # strings
        self.target = target
        self.prereq_list = prereq_list
        self.recipe_list = recipe_list

    def __str__(self):
        return "%s: %s" % (self.target, ",".join(self.prereq_list))

    def get_pos(self):
        # TODO
        return ((0,0),"/dev/null")

class RuleDB:
    # TODO need to better handle built-in rules
    pseudo_targets = [ ".PHONY" ]

    def __init__(self):
        self.rules = {}

        # first rule added becomes the default
        self.default = None

    def add(self, rule):
        # ha ha type checking
        assert isinstance(rule,Rule), type(rule)
        assert rule.target

        if self.default is None:
            self.default = rule
    
        if rule.target in self.rules:
            warning_message(rule.get_pos(), "overriding rule \"%s\"" % (rule.target, ))

        self.rules[rule.target] = rule
        
    def get(self, target):
        return self.rules[target]

    def __str__(self):
        return ",".join(self.rules.keys())

    def graph(self, graphname):
        # Build a graphviz dot file. This is the 2nd biggest reason I made this
        # whole silly program.

        dotfilename = graphname + "-graph.dot"
        with open(dotfilename,"w") as outfile:
            outfile.write("digraph %s {\n" % graphname)

            for target,rule in self.rules.items():
                # add the nodes 
                if target in self.pseudo_targets:
                    continue
                outfile.write("\t\"%s\"\n" % target)

            for target,rule in self.rules.items():
                # add the edges
                if target in self.pseudo_targets:
                    continue
                for p in rule.prereq_list:
                    outfile.write("\t\"%s\" -> \"%s\"\n" % (target, p))

            outfile.write("}\n")
        

