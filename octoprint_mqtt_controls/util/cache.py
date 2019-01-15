from __future__ import absolute_import

from functools import wraps


class cached_property(object):
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def cached_call(func):
    """Cache result of first call and return it on sequential calls"""
    result = {}

    @wraps(func)
    def wrapper():
        if not result.get('res'):
            result['res'] = func()
        return result['res']

    return wrapper
