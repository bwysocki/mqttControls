from __future__ import absolute_import

from .api import APIRequestCommand
from .download_file import DownloadFile

COMMANDS = (
    APIRequestCommand,
    DownloadFile,
)
