# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2014-2025 David Poole davep@mbuf.com david.poole@ericsson.com

import logging
import os

logger = logging.getLogger("pymake.rules")
#logger.setLevel(level=logging.DEBUG)

from pymake.error import *
from pymake.html import save_rules
import pymake.constants as constants

_debug = True

def _rule_sanity(pos, prereq_list, assignment):
    # if we have a prereq list, we cannot have an assignment
    # if we have an assignment, we cannot have a prereq list
    if prereq_list:
        assert not assignment, pos
    elif assignment:
        assert not prereq_list, pos

class Rule:
    # A Rule contains a target (string) and the prereqs (array of string).
    # Rule contains a RecipeList from the Symbol hierarchy but don't want to 
    # pull symbol.py in here (to keep pymake.py a little more clean).
    def __init__(self, target, prereq_list, recipe_list, assignment, pos):
        # ha ha type checking
        # target is string and prereq_list[] is array of strings
        # target can be None to handle rules without a target which GNU Make allows
        if target is not None:
            assert ' ' not in target
            assert '\t' not in target
            assert target
        assert all( (isinstance(s,str) for s in prereq_list) )
        _ = recipe_list.makefile

        logger.debug("create rule target=%r at %r", target, pos)
        self.target = target
        self.prereq_list = list(prereq_list)
        self.recipe_list = recipe_list
        self.assignment_list = [assignment] if assignment else []

        _rule_sanity(pos, prereq_list, assignment)

        # need to pass in an explict pos because the target is a string not a
        # Symbol.
        self.pos = pos

    def __str__(self):
        target = "" if self.target is None else self.target
        return "%s : %s" % (target, " ".join(self.prereq_list))

    def makefile(self):
        s = "".join([ "%s:%s\n" % (self.target,a.makefile()) for a in self.assignment_list]) 
        s += "%s : %s\n%s" % (self.target, " ".join(self.prereq_list), self.recipe_list.makefile())
        return s

    def get_pos(self):
        return self.pos

    def add_recipe(self, recipe):
        logger.debug("add recipe to rule=%r", self.target)
        self.recipe_list.append(recipe)

    def add_assignment(self, assignment):
        logger.debug("add assignment to rule=%r", self.target)
        self.assignment_list.append(assignment)

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
        # key: target (python string)
        # value: instance of class Rule
        self.rules = {}

        # first rule added becomes the default
        self.default = None

    def add(self, target, prereq_list, recipe_list, assignment, pos):

        # ha ha type checking
        _ = recipe_list.makefile

        logger.debug("add rule target=%r at %r", target, pos)

        if not target:
            # TODO
            breakpoint()
            assert rule.target

        if target == ".PHONY":
            raise NotImplementedError(target)
        elif target == ".PRECIOUS":
            raise NotImplementedError(target)

        _rule_sanity(pos, prereq_list, assignment)

        # do we currently have a rule already with this target?
        rule = self.rules.get(target,None)
        if not rule:
            # create new
            rule = Rule(target, prereq_list, recipe_list, assignment, pos)
        else:
            # could be an update or could be an overwrite
            #
            # If we don't have an assignment arg, and we've already seen some recipes,
            # then we have a new rule.
            if not assignment and len(rule.recipe_list):
                # overwrite
                warning_message(pos, "overriding recipe for target '%s'" % target )
                warning_message(rule.get_pos(), "ignoring old recipe for target '%s'" % target)

                rule = Rule(target, prereq_list, recipe_list, assignment, pos)
            else:
                # update existing rule
                if recipe_list:
                    [rule.add_recipe(r) for r in recipe_list]
                elif assignment:
                    rule.add_assignment(assignment)

        self.rules[rule.target] = rule

        if self.default is None:
            self.default = rule.target

        return rule
    
        
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

