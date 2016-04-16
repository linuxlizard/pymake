__all__ = [ "SourceFile" ]

class Source(object):
    def __init__(self, name="(none)"):
        self.name = name
        self.file_lines = []

    def load(self):
        pass

class SourceFile(Source):
    def __init__(self, filename):
        super().__init__(filename)

    def load(self):
        with open(self.name,'r') as infile :
            self.file_lines = infile.readlines()

# TODO read from io.StringIO ?

