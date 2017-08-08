from __future__ import absolute_import

import sys
if sys.version_info[:2] < (2, 7):
    m = "Python 2.7 or later is required for DyNetx (%d.%d detected)."
    raise ImportError(m % sys.version_info[:2])
del sys

import dynetx.classes
from dynetx.classes import *
from dynetx.classes.function import *

import dynetx.readwrite
from dynetx.readwrite import *

import dynetx.utils
from dynetx.utils import *