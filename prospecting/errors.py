#!/usr/bin/env python


class ProspectingException(Exception):
    """Base class for exceptions."""
    pass


class AssertError(ProspectingException):
    """Raised when attempts to asset value"""

    def __init__(self, err):
        self.err = err
        print('AssertionError: {0}'.format(self.err))
        print('No columns in headerrow. Add columns to sheet or pass headerrow=None.')
        print('Check self.data for malformed response (no columns set).')
