import io

__all__ = [ "SourceFile" ]

class Source(object):
    def __init__(self, name):
        self.name = name
        self.file_lines = []

    def load(self):
        # child class must implement
        raise NotImplementedError

class SourceFile(Source):
    def load(self):
        with open(self.name, 'r') as infile :
            self.file_lines = infile.readlines()


class SourceString(Source):
    def __init__(self, input_str):
        super().__init__("stringio")
        self.infile = io.StringIO(input_str)       

    def load(self):
        self.file_lines = self.infile.readlines()

