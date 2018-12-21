from __future__ import absolute_import

from .base import ApiReportCommand


class PrinterStateCommand(ApiReportCommand):
    command_name = 'printer_state'
    request_method = 'GET'
    api_endpoint = '/api/printer'
