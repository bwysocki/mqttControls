from functools import partial
from urllib import urlencode, quote_plus

from mock import patch


class cached_property(object):
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


# TODO: think about a better way of patching or replacing urlencode
def urlencode_safe(query, doseq=0, safe=''):
    with patch('urllib.quote_plus', new=partial(quote_plus, safe=safe)):
        return urlencode(query, doseq=doseq)
