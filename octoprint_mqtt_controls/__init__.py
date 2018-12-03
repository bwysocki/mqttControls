# coding=utf-8
from __future__ import absolute_import

import json
from urlparse import urljoin
from collections import Mapping

from octoprint.plugin import StartupPlugin
from octoprint.settings import settings
import requests

CONTROLS_TOPIC_NAME = 'octoprint/plugin/mqtt/controls'
# TODO: implement a setting which will control it


class MQTTControlsPlugin(StartupPlugin):
    @staticmethod
    def _create_api_session(api_key=None):
        s = requests.session()
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-Api-Key'] = api_key
        s.headers.update()
        return s

    def _get_url(self, endpoint):
        return urljoin(self._api_base, endpoint)

    def on_after_startup(self):
        helpers = self._plugin_manager.get_helpers('mqtt', 'mqtt_subscribe')
        mqtt_subscribe = helpers.get('mqtt_subscribe')
        if mqtt_subscribe:
            self._logger.info('Connecting to mqtt broker...')
            mqtt_subscribe(CONTROLS_TOPIC_NAME, self._on_mqtt_subscription)
            octo_settings = settings()
            self._api_session = self._create_api_session(
                api_key=octo_settings.get(['api', 'key'])
            )
            api_host = octo_settings.get(['server', 'host'])
            api_port = octo_settings.get(['server', 'port'])
            self._api_base = 'http://{}:{}'.format(api_host, api_port)
        else:
            self._logger.error("Could not retrieve 'mqtt_subscribe' helper.")

    def _on_mqtt_subscription(
            self, topic, message,
            retained=None, qos=None,
            *args, **kwargs
    ):
        self._logger.debug(
            'Received a control message at {topic}: {message}'.format(
                topic=topic,
                message=message
            )
        )

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

        request_method = parsed_message.get('method', 'GET')  # type: str
        request_url = self._get_url(parsed_message.get('endpoint', '/'))
        request_data = parsed_message.get('data')
        req = requests.Request(request_method, request_url)
        if request_method.lower() == 'post' and request_data:
            req.json = request_data

        resp = self._api_session.send(req.prepare())
        try:
            response_payload = resp.json()
        except ValueError:
            response_payload = resp.text

        self._logger.debug(
            'Received a response from {url} with code {code}:'
            'requested: {request_payload} - received: {response_payload}'
            .format(
                url=resp.request.url,
                code=resp.status_code,
                request_payload=resp.request.json or '',
                response_payload=response_payload,
            ),
        )


__plugin_name__ = 'MQTT Controls'
__plugin_implementation__ = MQTTControlsPlugin()
