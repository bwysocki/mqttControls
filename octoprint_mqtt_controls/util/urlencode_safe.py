from functools import partial
from urllib import urlencode, quote_plus

from mock import patch


# TODO: think about a better way of patching or replacing urlencode
def urlencode_safe(query, doseq=0, safe=''):
    with patch('urllib.quote_plus', new=partial(quote_plus, safe=safe)):
        return urlencode(query, doseq=doseq)
