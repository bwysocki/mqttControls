from __future__ import absolute_import

from .base import ApiReportCommand


class JobStateCommand(ApiReportCommand):
    COMMAND_NAME = 'job_state'
    REQUEST_METHOD = 'GET'
    API_ENDPOINT = '/api/job'
    REPORT_TOPIC = 'octoprint-controls/state/job'
