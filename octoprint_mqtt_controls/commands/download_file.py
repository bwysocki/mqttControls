import hashlib
import os
from threading import Event, Lock, Thread
from urllib import urlretrieve

from .base import CommandBase

_DOWNLOAD_THREADS = dict()
_DOWNLOAD_THREADS_LOCK = Lock()


def _set_download_thread(uid, thread):
    with _DOWNLOAD_THREADS_LOCK:
        _DOWNLOAD_THREADS[uid] = thread


def _pop_download_thread(uid):
    with _DOWNLOAD_THREADS_LOCK:
        return _DOWNLOAD_THREADS.pop(uid, None)


class StopDownload(Exception):
    """Raised on forced download stop"""
    def __init__(self, uid):
        self.message = 'Download %r has been forcefully stopped' % uid


class DownloadThread(Thread):
    """
    A Thread object for downloading a file

    Attributes:
        uid - unique id of the download
        url - file download url
        filename - name of the downloaded file
        checksum - md5 checksum of the downloaded file
    """
    def __init__(self, uid, url, filename, checksum, report_func):
        """
        Create a DownloadThread

        :param uid: unique id of the download
        :param url: file download url
        :param filename: name of the downloaded file
        :param checksum: md5 checksum of the downloaded file
        :param report_func: function used for progress reporting
        """
        self.uid = uid
        self.url = url
        self.filename = filename
        self.checksum = checksum

        self._report_func = report_func

        self._should_stop = Event()

        super(DownloadThread, self).__init__()

    def schedule_to_stop(self):
        """Schedule the thread to stop"""
        self._should_stop.set()

    def _report_progress(self, block_count, block_size, total_size):
        progress = min(
            int(round(block_count * block_size / float(total_size) * 100)),
            100
        )
        self._report_func({
            'uid': self.uid,
            'progress': progress
        })

    def _report_failure(self, exception):
        self._report_func({
            'uid': self.uid,
            'progress': 'failed',
            'reason': repr(exception)
        })

    def _report_success(self):
        self._report_func({
            'uid': self.uid,
            'progress': 'verified',
        })

    def _reporthook(self, *args):
        """Used as reporthook callback argument in `urllib.urlretrieve`"""
        if self._should_stop.is_set():
            raise StopDownload

        self._report_progress(*args)

    def _verify_file_hash(self, filename=None):
        """
        Calculate hash of the downloaded file and compare it to the given
        checksum.
        Raise ValueError if checksums do not match.
        """
        filename = filename or self.filename
        md5_hash = hashlib.md5()
        with open(filename, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)

        if not self.checksum == md5_hash.hexdigest():
            raise ValueError('File checksums do not match')
        self._report_success()

    def run(self):
        try:
            filename, headers = urlretrieve(
                self.url, self.filename, self._reporthook)
            self._verify_file_hash(filename)
        except Exception as e:
            self._report_failure(e)
            raise e


class DownloadFile(CommandBase):
    subtopic = 'download-file'
    report_subtopic = 'download-file/progress'

    def _get_file_path(self, filename):
        """Get full path to the target download file"""
        download_location = self._settings.get(['downloadLocation'])
        return os.path.join(download_location, filename)

    def execute(self, topic, payload, *args, **kwargs):
        uid = payload['uid']
        timestamp = payload['timestamp']

        if payload.get('stop'):
            download_thread = _pop_download_thread(uid)
            if download_thread is not None:
                download_thread.schedule_to_stop()
                return

        try:
            url = payload['url']
            filename = payload['filename']
            checksum = payload['checksum']
        except KeyError:
            self._logger.error(
                'Invalid command format: {payload}'.format(payload=payload)
            )
        else:
            download_thread = DownloadThread(
                uid,
                url,
                self._get_file_path(filename),
                checksum,
                self.report
            )
            _set_download_thread(uid, download_thread)
            download_thread.start()
