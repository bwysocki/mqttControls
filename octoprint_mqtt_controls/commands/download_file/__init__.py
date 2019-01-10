from __future__ import absolute_import

import os
from threading import Lock

from ..base import CommandBase
from .download_thread import DownloadThread

_DOWNLOAD_THREADS = dict()
_DOWNLOAD_THREADS_LOCK = Lock()


def _set_download_thread(uid, thread):
    with _DOWNLOAD_THREADS_LOCK:
        _DOWNLOAD_THREADS[uid] = thread


def _pop_download_thread(uid):
    with _DOWNLOAD_THREADS_LOCK:
        return _DOWNLOAD_THREADS.pop(uid, None)


class DownloadFile(CommandBase):
    subtopic = 'download-file/command'
    report_subtopic = 'download-file/report'

    def _get_file_path(self, filename):
        """Get full path to the target download file"""
        return os.path.join(self.plugin_instance.uploads_location, filename)

    def execute(self, topic, payload, *args, **kwargs):
        uid = payload['uid']
        timestamp = payload['timestamp']

        if payload.get('stop'):
            download_thread = _pop_download_thread(uid)
            if download_thread is not None:
                download_thread.schedule_to_stop()
                self._logger.info('Stopped download #%s' % uid)
                return

        try:
            url = payload['url']
            filename = payload['filename']
        except KeyError:
            self._logger.error(
                'Invalid command format: {payload}'.format(payload=payload)
            )
        else:
            md5 = payload.get('md5')
            download_thread = DownloadThread(
                uid,
                timestamp,
                url,
                self._get_file_path(filename),
                md5,
                self.report
            )
            _set_download_thread(uid, download_thread)
            download_thread.start()
            self._logger.info(
                'Started download #%s. File: %s' % (uid, filename)
            )
