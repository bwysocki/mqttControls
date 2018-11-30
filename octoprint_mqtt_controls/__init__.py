# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

CONTROLS_TOPIC_NAME = 'octoprint/plugin/mqtt/controls'


class MQTTControlsPlugin(octoprint.plugin.StartupPlugin):
    def on_after_startup(self):
        helpers = self._plugin_manager.get_helpers('mqtt', 'mqtt_subscribe')
        subscribe = helpers.get('mqtt_subscribe')
        if subscribe:
            self._logger.info('Connecting to mqtt broker...')
            subscribe(CONTROLS_TOPIC_NAME, self._on_mqtt_subscription)
        else:
            self._logger.error("Could not retrieve 'mqtt_subscribe' helper.")

    def _on_mqtt_subscription(self, topic, message, retained=None, qos=None, *args, **kwargs):
        self._logger.info("Received a control message - {topic}: {message}".format(**locals()))


__plugin_name__ = 'MQTT Controls'
__plugin_implementation__ = MQTTControlsPlugin()
