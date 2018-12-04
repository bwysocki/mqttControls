from __future__ import absolute_import

from .base import ApiReportCommand


class PrinterStateCommand(ApiReportCommand):
    COMMAND_NAME = 'printer_state'
    REQUEST_METHOD = 'GET'
    API_ENDPOINT = '/api/printer'
    REPORT_TOPIC = 'octoprint-controls/state/printer'
