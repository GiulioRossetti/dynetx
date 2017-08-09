"""
Miscellaneous Helpers for DyNetx.

These are not imported into the base networkx namespace but
can be accessed, for example, as

>>> import dynetx
>>> dyntex.utils.is_string_like('spam')
True
"""
#    Copyright (C) 2004-2015 by
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
import sys
import uuid
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
        if isinstance(x, unicode):
            return x
        else:
            # Note, this will not work unless x is ascii-encoded.
            # That is good, since we should be working with unicode anyway.
            # Essentially, unless we are reading a file, we demand that users
            # convert any encoded strings to unicode before using the library.
            #
            # Also, the str() is necessary to convert integers, etc.
            # unicode(3) works, but unicode(3, 'unicode-escape') wants a buffer.
            #
            return unicode(str(x), 'unicode-escape')
else:
    def make_str(x):
        """Return the string representation of t."""
        return str(x)


def generate_unique_node():
    """ Generate a unique node label."""
    return str(uuid.uuid1())