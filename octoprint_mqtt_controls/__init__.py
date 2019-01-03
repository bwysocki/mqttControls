# coding=utf-8
from __future__ import absolute_import

import os
import json
from urlparse import urljoin
from collections import Mapping

from octoprint.plugin import SettingsPlugin, StartupPlugin
from octoprint.plugin.core import PluginCantInitialize
from octoprint.settings import settings
import requests

from .commands import COMMANDS
from .util import cached_property, urlencode_safe

REST_API_SUBTOPIC = 'mqtt-rest-api/'
RESPONSE_SUBTOPIC = 'control-response/'


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

    def get_settings_defaults(self):
        return {
            'downloadLocation': os.path.expanduser(
                '~/.octoprint/downloads'
            )
        }

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
        download_location = self._settings.get(['downloadLocation'])
        if not os.path.exists(download_location):
            os.makedirs(download_location)

    def on_after_startup(self):
        self._create_file_download_directory()

        self._logger.info('Connecting to mqtt broker...')

        mqtt_plugin_info = self._plugin_manager.get_plugin_info('mqtt')
        if not mqtt_plugin_info:
            raise PluginCantInitialize(
                self._plugin_name,
                'Cannot get implementation of OctoPrint-MQTT plugin'
            )
        self.base_topic = mqtt_plugin_info.implementation._settings.get([
            'publish', 'baseTopic'
        ])

        helpers = self._plugin_manager.get_helpers(
            'mqtt', 'mqtt_subscribe', 'mqtt_publish')
        mqtt_subscribe = helpers.get('mqtt_subscribe')
        mqtt_publish = helpers.get('mqtt_publish')

        if not mqtt_publish:
            raise PluginCantInitialize(
                self._plugin_name,
                "Cannot get 'mqtt_subscribe' helper method "
                "from OctoPrint-MQTT plugin"
            )
        self.mqtt_publish = mqtt_publish

        if not mqtt_subscribe:
            raise PluginCantInitialize(
                self._plugin_name,
                "Cannot get 'mqtt_subscribe' helper method "
                "from OctoPrint-MQTT plugin"
            )
        octo_settings = settings()
        self.api_key = octo_settings.get(['api', 'key'])

        api_host = octo_settings.get(['server', 'host']) or '0.0.0.0'
        api_port = octo_settings.get(['server', 'port'])
        self.api_url_base = 'http://{}:{}'.format(api_host, api_port)

        self._subscribe_commands(mqtt_subscribe)


__plugin_name__ = 'MQTT Controls'
__plugin_implementation__ = MQTTControlsPlugin()
