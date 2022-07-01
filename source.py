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
    # TODO read from StringIO
    pass

