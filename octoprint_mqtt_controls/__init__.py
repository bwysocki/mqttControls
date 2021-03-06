# coding=utf-8
from __future__ import absolute_import

import os

from octoprint.plugin import SettingsPlugin, StartupPlugin
from octoprint.plugin.core import PluginCantInitialize
from octoprint.settings import settings as get_octoprint_settings

from .commands import COMMANDS
from .util import cached_property, urlencode_safe
from .settings import uploads_location

DEFAULT_UPLOAD_DIR = '~/.octoprint/uploads'


class MQTTControlsPlugin(SettingsPlugin, StartupPlugin):
    """
    Implementation of plugin. Connects mqtt to OctoPrint's REST API

    Attributes:
        mqtt_publish    helper method of OctoPrint-MQTT plugin,
                        used for publishing messages to the broker

        api_url_base    base of REST API URL

        controls_topic  MQTT topic used to retrieve control messages from

        response_topic  MQTT topic used to send responses to
    """
    def __init__(self):
        super(MQTTControlsPlugin, self).__init__()
        self.octoprint_settings = get_octoprint_settings()

    @cached_property
    def uploads_location(self):
        return os.path.expanduser(
            self.octoprint_settings.get(['folder', 'uploads'])
            or DEFAULT_UPLOAD_DIR
        )

    def _subscribe_commands(self, mqtt_subscribe):
        for command_class in COMMANDS:
            command = command_class(self)
            mqtt_subscribe(command.topic, command)
            self._logger.debug(
                'Subscribed command {command_name!r} to topic {topic!r}'
                .format(
                    command_name=command_class.__name__,
                    topic=command.topic
                )
            )

    def _create_file_download_directory(self):
        location = uploads_location()
        if not os.path.exists(location):
            os.makedirs(location)

            self._logger.info(
                'Created directory for file uploads: %r' % location
            )

    def on_after_startup(self):
        self._create_file_download_directory()

        self._logger.info('Connecting to mqtt broker...')

        mqtt_plugin_info = self._plugin_manager.get_plugin_info('mqttaws')
        if not mqtt_plugin_info:
            raise PluginCantInitialize(
                self._plugin_name,
                'Cannot get implementation of OctoPrint-MQTT plugin'
            )
        self.base_topic = mqtt_plugin_info.implementation._settings.get([
            'publish', 'baseTopic'
        ])

        helpers = self._plugin_manager.get_helpers(
            'mqttaws', 'mqttaws_subscribe', 'mqttaws_publish')
        mqtt_subscribe = helpers.get('mqttaws_subscribe')
        mqtt_publish = helpers.get('mqttaws_publish')

        if not mqtt_publish:
            raise PluginCantInitialize(
                self._plugin_name,
                "Cannot get 'mqttaws_subscribe' helper method "
                "from OctoPrint-MQTT plugin"
            )
        self.mqtt_publish = mqtt_publish

        if not mqtt_subscribe:
            raise PluginCantInitialize(
                self._plugin_name,
                "Cannot get 'mqttaws_subscribe' helper method "
                "from OctoPrint-MQTT plugin"
            )
        self._subscribe_commands(mqtt_subscribe)


__plugin_name__ = 'MQTT Controls'


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MQTTControlsPlugin()
