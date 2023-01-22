#!/usr/bin/env python3

import logging
import os

logger = logging.getLogger("pymake.rules")

from pymake.error import *

_debug = True

class Rule:
    # A Rule contains a target (string) and the prereqs (array of string).
    # Rule contains a RecipeList from the Symbol hierarchy but don't want to 
    # pull symbol.py in here (to keep pymake.py a little more clean).
    def __init__(self, target, prereq_list, recipe_list, pos):
        # target is string and prereq_list[] is array of strings
        self.target = target
        self.prereq_list = prereq_list
        self.recipe_list = recipe_list

        # need to pass in an explict pos because the target is a string not a
        # Symbol.
        self.pos = pos

    def __str__(self):
        return "%s: %s" % (self.target, ",".join(self.prereq_list))

    def get_pos(self):
        return self.pos

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

        if rule.target == ".PHONY":
            # TODO
            return

        if self.default is None:
            self.default = rule.target
    
        # GNU Make doesn't warn on this sort of thing but I want to see it.
        if rule.target in self.rules:
            warning_message(rule.get_pos(), "overriding rule \"%s\"" % (rule.target, ))

        self.rules[rule.target] = rule
        
    def get(self, target):
        # allow KeyError to propagate
        logger.debug("look up rule for target=\"%s\"", target)
        return self.rules[target]

    def get_default_target(self):
        assert self.default
        return self.default

    def walk_tree(self, target):
        # generator of rules to build a target, starting at ye bottom.
        # GNU Make handles prerequisites left to right. So basically in array
        # order.  TL;DR. Depth-Breadth first tree traversal.
        # TODO: how do I want to handle parallel builds someday?
        # TODO: loops in the digraph are possible?

        logger.debug("make target=\"%s\"", target)
        if os.path.exists(target):
            logger.debug("target=\"%s\" exists", target)
            return

        rule = self.get(target)
        for p in rule.prereq_list:
            yield from self.walk_tree(p)
        yield rule

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

        return dotfilename
        
