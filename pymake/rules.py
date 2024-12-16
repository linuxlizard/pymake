# SPDX-License-Identifier: GPL-2.0

import logging
import os

logger = logging.getLogger("pymake.rules")
#logger.setLevel(level=logging.DEBUG)

from pymake.error import *
from pymake.html import save_rules
import pymake.constants as constants

_debug = True

class Rule:
    # A Rule contains a target (string) and the prereqs (array of string).
    # Rule contains a RecipeList from the Symbol hierarchy but don't want to 
    # pull symbol.py in here (to keep pymake.py a little more clean).
    def __init__(self, target, prereq_list, recipe_list, pos):
        # ha ha type checking
        # target is string and prereq_list[] is array of strings
        # target can be None to handle rules without a target which GNU Make allows
        if target is not None:
            assert ' ' not in target
            assert '\t' not in target
            assert target
        assert all( (isinstance(s,str) for s in prereq_list) )

        logger.debug("create rule target=%r at %r", target, pos)
        self.target = target
        self.prereq_list = prereq_list
        self.recipe_list = recipe_list

        # need to pass in an explict pos because the target is a string not a
        # Symbol.
        self.pos = pos

    def __str__(self):
        target = "" if self.target is None else self.target
        return "%s <- %s" % (target, ",".join(self.prereq_list))

    def get_pos(self):
        return self.pos

    def add_recipe(self, recipe):
        logger.debug("add recipe to rule=%r", self)
        self.recipe_list.append(recipe)

    def graphviz_graph(self):
        if self.target is None:
            raise ValueError("cannot build a graphviz for rule without targets at pos=%r" % self.pos)

        title = self.target.replace("/","_").replace(".","_")
        dotfilename = self.target + ".dot"

        with open(dotfilename,"w") as outfile:
            outfile.write("digraph %s {\n" % title)

            outfile.write("\t\"%s\"\n" % self.target)

            for p in self.prereq_list:
                if p.startswith("/usr"):
                    continue
                outfile.write("\t\"%s\" -> \"%s\"\n" % (self.target, p))

            outfile.write("}\n")

class RuleDB:
    def __init__(self):
        self.rules = {}

        # first rule added becomes the default
        self.default = None

    def add(self, rule):
        # ha ha type checking
        logger.debug("add rule=%s at %r", rule, rule.get_pos())
        assert isinstance(rule,Rule), type(rule)

        if not rule.target:
            # TODO
            breakpoint()
            assert rule.target

        if rule.target == ".PHONY":
            # TODO
            return

        if self.default is None:
            self.default = rule.target
    
        # GNU Make doesn't warn on this sort of thing but I want to see it.
        if rule.target in self.rules and rule.prereq_list:
            warning_message(rule.get_pos(), "overriding rule \"%s\"" % (rule.target, ))

        self.rules[rule.target] = rule
        
    def get(self, target):
        # allow KeyError to propagate
        logger.debug("look up rule for target=\"%s\"", target)
        return self.rules[target]

    def get_default_target(self):
        if not self.default:
            raise IndexError

        return self.default

    def walk_tree(self, target):
        # generator of rules to build a target, starting at ye bottom.
        # GNU Make handles prerequisites left to right. So basically in array
        # order.  TL;DR. Depth-Breadth first tree traversal.
        # TODO: how do I want to handle parallel builds someday?
        # TODO: loops in the digraph are possible?

        logger.debug("find target=\"%s\"", target)
        if os.path.exists(target):
            logger.debug("target=\"%s\" exists", target)
            return

        rule = self.get(target)
        for p in rule.prereq_list:
            yield from self.walk_tree(p)
        yield rule

    def __str__(self):
        return ",".join(self.rules.keys())

    def html_graph(self, title, outfilename):
        save_rules(outfilename, self.rules)
            
    def graphviz_graph(self, title, dotfilename):
        # Build a graphviz dot file. This is the 2nd biggest reason I made this
        # whole silly program.

        with open(dotfilename,"w") as outfile:
            outfile.write("digraph %s {\n" % title)

            for target,rule in self.rules.items():
                # add the nodes 
                if target in constants.built_in_targets:
                    continue
                if target.startswith("/usr"):
                    continue
                outfile.write("\t\"%s\"\n" % target)

            for target,rule in self.rules.items():
                # add the edges
                if target in constants.built_in_targets:
                    continue
                for p in rule.prereq_list:
                    if p.startswith("/usr"):
                        continue
                    outfile.write("\t\"%s\" -> \"%s\"\n" % (target, p))

            outfile.write("}\n")

        return dotfilename

