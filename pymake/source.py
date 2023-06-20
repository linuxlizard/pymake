import io

from pymake.error import *

__all__ = [ "SourceFile" ]

class Source(object):
    def __init__(self, name):
        self.name = name
        self.file_lines = []

    def load(self):
        # child class must implement
        raise NotImplementedError

# 3.2 What Name to Give Your Makefile
#
# By default, when make looks for the makefile, it tries the following names,
# in order: GNUmakefile, makefile and Makefile.
#
# Normally you should call your makefile either makefile or Makefile. (We
# recommend Makefile because it appears prominently near the beginning of a
# directory listing, right near other important files such as README.) The
# first name checked, GNUmakefile, is not recommended for most makefiles. You
# should use this name if you have a makefile that is specific to GNU make, and
# will not be understood by other versions of make. Other make programs look
# for makefile and Makefile, but not GNUmakefile. 
#
class SourceFile(Source):
    default_names = ("GNUmakefile", "makefile", "Makefile")

    def __init__(self, name=None):
        super().__init__(name)

    def _load_default(self):
        for name in self.default_names:
            try:
                with open(name, 'r') as infile :
                    self.file_lines = infile.readlines()
                self.name = name
                return
            except FileNotFoundError:
                continue
        raise NoMakefileFound

    def load(self):
        if self.name is None:
            return self._load_default()

        with open(self.name, 'r') as infile :
            self.file_lines = infile.readlines()


class SourceString(Source):
    def __init__(self, input_str):
        super().__init__("...string")
        self.infile = io.StringIO(input_str)       

    def load(self):
        self.file_lines = self.infile.readlines()

