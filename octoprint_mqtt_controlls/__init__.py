# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

CONTROLLS_TOPIC_NAME = 'octoprint/plugin/mqtt/controlls'


class MQTTControllsPlugin(octoprint.plugin.StartupPlugin):
    def on_after_startup(self):
        helpers = self._plugin_manager.get_helpers("mqtt", "mqtt_subscribe")
        subscribe = helpers["mqtt_subscribe"]
        subscribe("octoprint/plugin/mqtt_test/sub", self._on_mqtt_subscription)

    def _on_mqtt_subscription(self, topic, message, retained=None, qos=None, *args, **kwargs):
        self._logger.info("Received a control message {topic}: {message}".format(**locals()))


__plugin_name__ = 'MQTT Controlls'
__plugin_implementation__ = MQTTControllsPlugin()
