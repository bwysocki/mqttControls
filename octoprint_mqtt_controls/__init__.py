# coding=utf-8
from __future__ import absolute_import

import json
import urlparse

import octoprint.plugin
import requests

CONTROLS_TOPIC_NAME = 'octoprint/plugin/mqtt/controls'
# TODO: implement a setting which will control it
REST_API_HOST = '127.0.0.1'


class MQTTControlsPlugin(octoprint.plugin.StartupPlugin):
    @staticmethod
    def _create_api_session():
        s = requests.session()
        s.headers.update({'Content-Type': 'application/json'})
        return s

    @staticmethod
    def _get_url(endpoint):
        return urlparse.urljoin(REST_API_HOST, endpoint)

    def on_after_startup(self):
        helpers = self._plugin_manager.get_helpers('mqtt', 'mqtt_subscribe')
        subscribe = helpers.get('mqtt_subscribe')
        if subscribe:
            self._logger.info('Connecting to mqtt broker...')
            subscribe(CONTROLS_TOPIC_NAME, self._on_mqtt_subscription)
            # TODO: implement authentication
            self._api_session = self._create_api_session()
        else:
            self._logger.error("Could not retrieve 'mqtt_subscribe' helper.")

    def _on_mqtt_subscription(
            self, topic, message,
            retained=None, qos=None,
            *args, **kwargs
    ):
        self._logger.debug(
            'Received a control message - {topic}: {message}'.format(
                topic=topic,
                message=message
            )
        )
        parsed_message = json.loads(message)

        request_method = parsed_message.get('method', 'GET'),  # type: str
        request_url = self._get_url(parsed_message.get('endpoint', '/'))
        request_data = parsed_message.get('data')
        req = requests.Request(request_method, request_url)
        if request_method.lower() == 'post' and request_data:
            req.json = request_data

        self._logger.debug(
            'Sending a {method} request to {url}'.format(
                method=request_method,
                url=request_url,
            ),
            extra={'data': request_data}
        )

        resp = self._api_session.send(req.prepare())
        self._logger.debug(
            'Received a response with code {code}'.format(
                code=resp.status_code
            ),
            extra=resp.json()
        )


__plugin_name__ = 'MQTT Controls'
__plugin_implementation__ = MQTTControlsPlugin()
