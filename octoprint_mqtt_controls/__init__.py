# coding=utf-8
from __future__ import absolute_import

import json
from urlparse import urljoin
from collections import Mapping

from octoprint.plugin import StartupPlugin
from octoprint.settings import settings
import requests

from .commands import get_command

CONTROLS_TOPIC_NAME = 'octoprint/plugin/mqtt/controls'
# TODO: implement a setting which will control it


class MQTTControlsPlugin(StartupPlugin):
    @staticmethod
    def _create_api_session(api_key=None):
        s = requests.Session()
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-Api-Key'] = api_key
        s.headers.update(headers)
        return s

    def _get_url(self, endpoint):
        return urljoin(self._api_url_base, endpoint)

    def on_after_startup(self):
        helpers = self._plugin_manager.get_helpers(
            'mqtt', 'mqtt_subscribe', 'mqtt_publish')
        mqtt_subscribe = helpers.get('mqtt_subscribe')
        mqtt_publish = helpers.get('mqtt_publish')

        if mqtt_subscribe:
            self._logger.info('Connecting to mqtt broker...')
            mqtt_subscribe(CONTROLS_TOPIC_NAME, self._on_mqtt_subscription)

            octo_settings = settings()
            self._api_session = self._create_api_session(
                api_key=octo_settings.get(['api', 'key'])
            )

            api_host = octo_settings.get(['server', 'host']) or '0.0.0.0'
            api_port = octo_settings.get(['server', 'port'])
            self._api_url_base = 'http://{}:{}'.format(api_host, api_port)

            self._mqtt_publish = mqtt_publish
        else:
            self._logger.error("Could not retrieve 'mqtt_subscribe' helper.")

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
                command = command_class(
                    self._api_session,
                    self._api_url_base,
                    self._mqtt_publish,
                    timestamp,
                    parsed_message.get('options'),
                    logger=self._logger
                )
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

        resp = self._api_session.request(
            request_method,
            request_url,
            json=request_data
        )
        try:
            response_payload = resp.json()
        except ValueError:
            response_payload = resp.text

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
