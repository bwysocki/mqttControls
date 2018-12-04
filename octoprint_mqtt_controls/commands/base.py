from abc import ABCMeta, abstractmethod, abstractproperty
from logging import getLogger

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
    def command_name(self):
        """Used for command search"""

    @abstractmethod
    def execute(self):
        """Command action"""
