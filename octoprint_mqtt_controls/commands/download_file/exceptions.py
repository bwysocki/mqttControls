class StopDownload(Exception):
    """Raised on forced download stop"""
    def __init__(self, uid):
        self.message = 'Download %r has been forcefully stopped' % uid


class ChecksumVerificationError(Exception):
    """Raised on checksum verification fail"""
    def __init__(self, expected, calculated):
        self.message = 'Checksums do not match: {!r} != {!r}'.format(
            expected, calculated)
