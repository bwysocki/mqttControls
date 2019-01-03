import json
from abc import ABCMeta, abstractmethod, abstractproperty

from ..util import cached_property


class CommandBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, plugin_instance):
        self.plugin_instance = plugin_instance
        self._logger = self.plugin_instance._logger
        self._settings = self.plugin_instance._settings

    @abstractproperty
    def subtopic(self):
        """Subtopic for command to subscribe to"""

    @cached_property
    def topic(self):
        return self.plugin_instance.base_topic + self.subtopic

    @abstractproperty
    def report_subtopic(self):
        """Subtopic for command status reporting"""

    @cached_property
    def report_topic(self):
        return self.plugin_instance.base_topic + self.report_subtopic

    def report(self, payload):
        self.plugin_instance.mqtt_publish(self.report_topic, payload)

    @abstractmethod
    def execute(self, topic, payload, *args, **kwargs):
        """Command action"""

    def __call__(self, topic, payload, *args, **kwargs):
        try:
            parsed_payload = json.loads(payload)
        except ValueError:
            self._logger.error(
                'Could not parse message at topic {topic} as JSON: {payload!r}'
                .format(topic=topic, payload=payload)
            )
        else:
            if (
                'uid' not in parsed_payload
                or 'timestamp' not in parsed_payload
            ):
                self._logger.error("'uid' and 'timestamp' fields are required")
            else:
                self.execute(topic, parsed_payload, *args, **kwargs)
