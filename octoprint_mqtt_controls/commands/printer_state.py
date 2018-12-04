from urlparse import urljoin

from .base import CommandBase


class PrinterStateCommand(CommandBase):
    command_name = 'printer_state'

    STATUS_TOPIC = 'octoprint-controls/printer-state'

    API_ENDPOINT = 'api/printer'
    REQUEST_METHOD = 'GET'

    def execute(self):
        resp = self.api_session.request(
            self.REQUEST_METHOD,
            urljoin(self.api_url_base, self.API_ENDPOINT),
        )
        payload = resp.json()
        self.mqtt_publish(
            self.STATUS_TOPIC,
            payload,
            retained=True,
            qos=0,
            allow_queueing=True
        )
