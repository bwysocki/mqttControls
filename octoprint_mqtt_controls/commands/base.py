from abc import ABCMeta, abstractmethod, abstractproperty
from logging import getLogger
from urlparse import urljoin

_default_logger = getLogger(__name__)


class CommandBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, plugin_instance):
        self.plugin_instance = plugin_instance

    @abstractproperty
    def command_name(self):
        """Used for command search"""

    @abstractmethod
    def execute(self):
        """Command action"""


class ApiReportCommand(CommandBase):
    """
    Makes an API request with given `request_method` to given `api_endpoint`
    and redirects response to the plugin report MQTT topic
    """

    @abstractproperty
    def request_method(self):
        """HTTP request method"""

    @abstractproperty
    def api_endpoint(self):
        """API endpoint address"""

    def execute(self):
        resp = self.plugin_instance.api_session.request(
            self.request_method,
            urljoin(self.plugin_instance.api_url_base, self.api_endpoint)
        )
        self.plugin_instance._logger.debug(
            "HTTP {method} {path}: {status} - {text!r}".format(
                method=resp.request.method,
                path=resp.request.path_url,
                status=resp.status_code,
                text=resp.text
            )
        )

        try:
            payload = resp.json()
        except ValueError:
            payload = resp.text

        self.plugin_instance.mqtt_publish(
            self.plugin_instance.response_topic,
            payload,
            retained=True,
            qos=0,
            allow_queueing=True
        )
