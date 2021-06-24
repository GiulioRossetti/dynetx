"""
Miscellaneous Helpers for DyNetx.
"""
#    Copyright (C) 2004-2015 by
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
import sys
# itertools.accumulate is only available on Python 3.2 or later.
#
# Once support for Python versions less than 3.2 is dropped, this code should
# be removed.
try:
    from itertools import accumulate
except ImportError:
    import operator

    # The code for this function is from the Python 3.5 documentation,
    # distributed under the PSF license:
    # <https://docs.python.org/3.5/library/itertools.html#itertools.accumulate>
    def accumulate(iterable, func=operator.add):
        it = iter(iterable)
        try:
            total = next(it)
        except StopIteration:
            return
        yield total
        for element in it:
            total = func(total, element)
            yield total

__author__ = '\n'.join(['Aric Hagberg (hagberg@lanl.gov)',
                        'Dan Schult(dschult@colgate.edu)',
                        'Ben Edwards(bedwards@cs.unm.edu)'])


PY2 = sys.version_info[0] == 2
if PY2:
    def make_str(x):
        """Return the string representation of t."""
        if isinstance(x, str):
            return x
        else:
            return str(str(x), 'unicode-escape')
else:
    def make_str(x):
        """Return the string representation of t."""
        return str(x)
