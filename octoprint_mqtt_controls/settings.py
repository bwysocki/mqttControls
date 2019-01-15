from __future__ import absolute_import

import os

from octoprint.settings import settings

from .util import cached_call

DEFAULT_UPLOADS_LOCATION = '~/.octoprint/uploads'


@cached_call
def uploads_location():
    octoprint_settings = settings()
    return os.path.expanduser(
        octoprint_settings.get(['folder', 'uploads'])
        or DEFAULT_UPLOADS_LOCATION
    )
