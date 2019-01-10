from __future__ import absolute_import

from enum import Enum


class Progress(Enum):
    error = 'error'
    stopped = 'stopped'
    success = 'success'
