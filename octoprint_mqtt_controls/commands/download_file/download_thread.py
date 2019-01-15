from __future__ import absolute_import

import hashlib
import os
from threading import Event, Thread
from urllib import urlretrieve

from ...settings import uploads_location
from ...util import api_request, cached_property
from .exceptions import ChecksumVerificationError, StopDownload
from .progress import Progress


class DownloadThread(Thread):
    """
    A Thread object for downloading a file

    Attributes:
        uid - unique id of the download
        timestamp - when command was issued
        url - file download url
        filename - name of the downloaded file
        md5 - md5 checksum of the downloaded file
    """

    def __init__(self, uid, timestamp, url, filename, md5, report_func):
        """
        Create a DownloadThread

        :param uid: unique id of the download
        :param timestamp: when command was issued
        :param url: file download url
        :param filename: name of the downloaded file
        :param md5: md5 checksum of the downloaded file
        :param report_func: function used for progress reporting
        """
        self.uid = uid
        self.timestamp = timestamp
        self.url = url
        self.filename = filename
        self.md5 = md5

        self._report_func = report_func

        self._should_stop = Event()

        super(DownloadThread, self).__init__()

    @cached_property
    def _file_path(self):
        """Get full path to the target download file"""
        return os.path.join(uploads_location(), self.filename)

    def schedule_to_stop(self):
        """Schedule the thread to stop"""
        self._should_stop.set()

    def _report(self, data):
        report_data = {
            'uid': self.uid,
            'timestamp': self.timestamp,
        }
        report_data.update(data)

        self._report_func(report_data)

    def _report_failure(self, reason):
        self._report({
            'progress': Progress.error.value,
            'reason': reason
        })

    def _report_success(self):
        self._report({'progress': Progress.success.value})

    def _report_stopped(self):
        self._report({'progress': Progress.stopped.value})

    def _report_progress(self, block_count, block_size, total_size):
        progress = min(
            int(round(block_count * block_size / float(total_size) * 100)),
            100
        ) if total_size > 0 else None
        self._report({'progress': progress})

    def _reporthook(self, *args):
        """Used as reporthook callback argument in `urllib.urlretrieve`"""
        if self._should_stop.is_set():
            raise StopDownload

        self._report_progress(*args)

    def _verify_file_hash(self, file_path=None):
        """
        Calculate hash of the downloaded file and compare it to the given
        checksum (if provided).
        Raise `ChecksumVerificationError` if checksums do not match.
        """
        if not self.md5:
            return

        file_path = file_path or self._file_path
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)

        calculated_md5 = md5_hash.hexdigest()
        if not self.md5 == calculated_md5:
            raise ChecksumVerificationError(
                expected=self.md5,
                calculated=calculated_md5
            )

    def _printjob_request(self):
        return api_request(
            'POST',
            '/api/files/local',
            data={
                'select': True,
                'print': True,
            },
            files={
                'file': (
                    self.filename,
                    open(self._file_path, 'rb'),
                    'application/octet-stream',
                )
            },
        )

    def run(self):
        try:
            file_path, headers = urlretrieve(
                self.url, self._file_path, self._reporthook)
            self._verify_file_hash(file_path)
        except StopDownload:
            self._report_stopped()
        except Exception as e:
            self._report_failure(str(e))
        else:
            resp = self._printjob_request()
            if resp.ok:
                self._report_success()
            else:
                self._report_failure(resp.status)
