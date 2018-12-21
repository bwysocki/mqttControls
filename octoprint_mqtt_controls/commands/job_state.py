from __future__ import absolute_import

from .base import ApiReportCommand


class JobStateCommand(ApiReportCommand):
    command_name = 'job_state'
    request_method = 'GET'
    api_endpoint = '/api/job'
