from abc import ABCMeta, abstractmethod, abstractproperty
from logging import getLogger
from urlparse import urljoin

_default_logger = getLogger(__name__)


class CommandBase(object):
    __metaclass__ = ABCMeta

    def __init__(
        self,
        api_session,
        api_url_base,
        mqtt_publish,
        timestamp,
        options,
        logger=_default_logger
    ):
        self.api_session = api_session
        self.api_url_base = api_url_base
        self.mqtt_publish = mqtt_publish
        self.timestamp = timestamp
        self.options = options
        self.logger = logger

    @abstractproperty
    def COMMAND_NAME(self):
        """Used for command search"""

    @abstractmethod
    def execute(self):
        """Command action"""


class ApiReportCommand(CommandBase):
    """
    Makes an API request with given REQUEST_METHOD to given API_ENDPOINT
    and redirects response to REPORT_TOPIC MQTT topic
    """

    @abstractproperty
    def REQUEST_METHOD(self):
        """HTTP request method"""

    @abstractproperty
    def API_ENDPOINT(self):
        """API endpoint address"""

    @abstractproperty
    def REPORT_TOPIC(self):
        """MQTT topic where the API request result is redirected"""

    def execute(self):
        resp = self.api_session.request(
            self.REQUEST_METHOD,
            urljoin(self.api_url_base, self.API_ENDPOINT)
        )
        payload = resp.json()
        self.mqtt_publish(
            self.REPORT_TOPIC,
            payload,
            retained=True,
            qos=0,
            allow_queueing=True
        )
