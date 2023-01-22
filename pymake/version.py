#!/usr/bin/env python3

__all__ = [
    "Version",
]

# for now, focus on 4.1 compatibility
class Version(object):
    major = 4
    minor = 1

# major = 3
# minor = 81

    @classmethod
    def vstring(cls):
        return "%d.%d" % (cls.major, cls.minor)

    # TODO add methods, etc, to easily compare version numbers
