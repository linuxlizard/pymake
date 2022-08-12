# functions for the filesystem

from functions_base import Function, FunctionWithArguments
from todo import TODOMixIn

__all__ = [ "AbsPath", 
            "AddPrefix",
            "AddSuffix",
            "DirClass", 
            "FileClass",
            "JoinClass",
            "NotDirClass",
            "RealPath",
            "Suffix",
            "Wildcard",
        ]

class AbsPath(TODOMixIn, Function):
    name = "abspath"

class AddPrefix(TODOMixIn, FunctionWithArguments):
    name = "addprefix"

class AddSuffix(TODOMixIn, FunctionWithArguments):
    name = "addsuffix"

class DirClass(TODOMixIn, FunctionWithArguments):
    name = "dir"

class FileClass(TODOMixIn, FunctionWithArguments):
    name = "file"

class JoinClass(TODOMixIn, Function):
    name = "join"

class NotDirClass(TODOMixIn, FunctionWithArguments):
    name = "notdir"

class RealPath(TODOMixIn, FunctionWithArguments):
    name = "realpath"

class Suffix(TODOMixIn, FunctionWithArguments):
    name = "suffix"

class Wildcard(TODOMixIn, FunctionWithArguments):
    name = "wildcard"

