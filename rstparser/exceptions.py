#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

"""Project-specific exceptions that can be raised by RST parser.

"""

##################################################################
# Imports
from __future__ import absolute_import, print_function, unicode_literals


##################################################################
# Classes
class ParseError(Exception):
    """ Exception for parsing
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ActionError(Exception):
    """ Exception for illegal parsing action
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
