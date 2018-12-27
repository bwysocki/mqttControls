# coding=utf-8
from __future__ import absolute_import

import json
from urlparse import urljoin
from collections import Mapping

from octoprint.plugin import SettingsPlugin, StartupPlugin
from octoprint.plugin.core import PluginCantInitialize
from octoprint.settings import settings
import requests

from .commands import get_command
from .util import cached_property

CONTROLS_SUBTOPIC = 'mqtt-rest-api/'
RESPONSE_SUBTOPIC = 'control-response/'


class MQTTControlsPlugin(SettingsPlugin, StartupPlugin):
    """
    Implementation of plugin. Connects mqtt to OctoPrint's REST API

    Attributes:
        api_session     request.Session with a set of headers,
                        necessary for REST API connection.
                        Use it to send requests

        mqtt_publish    helper method of OctoPrint-MQTT plugin,
                        used for publishing messages to the broker

        api_url_base    base of REST API URL

        controls_topic  MQTT topic used to retrieve control messages from

        response_topic  MQTT topic used to send responses to
    """

    @cached_property
    def controls_topic(self):
        return self.base_topic + CONTROLS_SUBTOPIC

    @cached_property
    def response_topic(self):
        return self.base_topic + RESPONSE_SUBTOPIC

    @staticmethod
    def _create_api_session(api_key=None):
        s = requests.Session()
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-Api-Key'] = api_key
        s.headers.update(headers)
        return s

    def _get_url(self, endpoint):
        return urljoin(self.api_url_base, endpoint)

    def on_after_startup(self):
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
        mqtt_subscribe(self.controls_topic, self._on_mqtt_subscription)
        self._logger.debug('Subscribed to %s' % self.controls_topic)

        octo_settings = settings()
        self.api_session = self._create_api_session(
            api_key=octo_settings.get(['api', 'key'])
        )

        api_host = octo_settings.get(['server', 'host']) or '0.0.0.0'
        api_port = octo_settings.get(['server', 'port'])
        self.api_url_base = 'http://{}:{}'.format(api_host, api_port)

    def _on_mqtt_subscription(
            self, topic, message,
            retained=None, qos=None,
            *args, **kwargs
    ):
        try:
            parsed_message = json.loads(message)
        except ValueError:
            self._logger.error(
                'Could not parse the given message as JSON: {message}'.format(
                    message=message)
            )
            return

        if not isinstance(parsed_message, (Mapping, dict)):
            self._logger.debug(
                'Message is not a JSON-object: {parsed_message}'.format(
                    parsed_message=parsed_message
                )
            )
            return

        timestamp = parsed_message.get('timestamp')
        if timestamp is None:
            timestamp = '<unknown>'
            self._logger.warning(
                'Message passed without an identifying timestamp'
            )

        command_name = parsed_message.get('command')
        if command_name:
            try:
                command_class = get_command(command_name)
            except ValueError:
                self._logger.error(
                    'Received a command message {timestamp} '
                    'with invalid command name: {name}'
                    .format(
                        timestamp=timestamp,
                        name=command_name
                    )
                )
            else:
                self._logger.debug(
                    'Received a command message {timestamp} '
                    "with {command} command. Executing..."
                    .format(
                        timestamp=timestamp,
                        command=command_name
                    )
                )
                command = command_class(self)
                command.execute()
            return

        self._logger.debug(
            'Received a request message {timestamp} at {topic}: {message}'
            .format(
                timestamp=timestamp,
                topic=topic,
                message=parsed_message
            )
        )

        request_method = parsed_message.get('method', 'GET')  # type: str
        request_url = self._get_url(parsed_message.get('endpoint', '/'))
        request_data = parsed_message.get('data')

        resp = self.api_session.request(
            request_method,
            request_url,
            json=request_data
        )
        try:
            response_payload = resp.json()
        except ValueError:
            response_payload = resp.text

        self.mqtt_publish(self.response_topic, response_payload)

        self._logger.debug(
            'Response for message {timestamp} to {url} with code {code}:\n'
            "request body: '{request_body}'\n"
            "response: {response_payload}"
            .format(
                timestamp=timestamp,
                url=resp.request.url,
                code=resp.status_code,
                request_body=resp.request.body or '',
                response_payload=response_payload,
            ),
        )


__plugin_name__ = 'MQTT Controls'
__plugin_implementation__ = MQTTControlsPlugin()
