from __future__ import absolute_import

from .download_file import DownloadFile
from .api import APIRequestCommand

COMMANDS = (
    DownloadFile,
    APIRequestCommand,
)
