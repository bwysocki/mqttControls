from urlparse import urljoin

import requests
from octoprint.settings import settings as get_octoprint_settings

from .cache import cached_call


@cached_call
def api_url_base():
    octoprint_settings = get_octoprint_settings()
    api_host = octoprint_settings.get(['server', 'host']) or '0.0.0.0'
    api_port = octoprint_settings.get(['server', 'port'])
    return 'http://{}:{}'.format(api_host, api_port)


def get_endpoint_url(endpoint):
    """Get full url for the given"""
    return urljoin(api_url_base(), endpoint)


def api_request(method, endpoint, **kwargs):
    octoprint_settings = get_octoprint_settings()

    headers = {
        'X-Api-Key': octoprint_settings.get(['api', 'key'])
    }
    headers.update(
        kwargs.get('headers', ())
    )
    kwargs['headers'] = headers

    return requests.request(method, get_endpoint_url(endpoint), **kwargs)
