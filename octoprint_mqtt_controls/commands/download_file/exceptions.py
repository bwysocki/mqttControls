class StopDownload(Exception):
    """Raised on forced download stop"""
    def __init__(self, uid):
        super(StopDownload, self).__init__(
            'Download %r has been forcefully stopped' % uid
        )


class ChecksumVerificationError(Exception):
    """Raised on checksum verification fail"""
    def __init__(self, expected, calculated):
        super(ChecksumVerificationError, self).__init__(
            'Checksums do not match: {!r} != {!r}'.format(
                expected, calculated)
        )
