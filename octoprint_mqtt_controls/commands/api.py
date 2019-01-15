from __future__ import absolute_import

import requests
from octoprint.settings import settings

from .base import CommandBase
from ..util.api import get_endpoint_url

RESPONSE_SUBTOPIC = 'control-response/'


class APIRequestCommand(CommandBase):
    subtopic = 'mqtt-rest-api/'
    report_subtopic = 'control-response/'

    def __init__(self, *args, **kwargs):
        super(APIRequestCommand, self).__init__(*args, **kwargs)
        octoprint_settings = settings()
        self.api_session = self._create_api_session(
            octoprint_settings.get(['api', 'key'])
        )

    def _create_api_session(self, api_key=None):
        s = requests.Session()
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-Api-Key'] = api_key
        s.headers.update(headers)
        return s

    def execute(self, topic, payload, *args, **kwargs):
        uid = payload['uid']
        timestamp = payload['timestamp']
        method = payload.get('method', 'GET').upper()
        data = payload.get('data')

        endpoint = payload.get('endpoint')
        if not endpoint:
            self._logger.error(
                'Invalid command format: {payload}'.format(payload=payload)
            )
            return

        response = self.api_session.request(
            method,
            get_endpoint_url(endpoint),
            json=data
        )
        response_payload = response.text
        if response.headers['content-type'] == 'application/json':
            response_payload = response.json()

        self._logger.debug(
            'API request: HTTP {method} {endpoint} with data {data!r} - '
            '{code} headers: {response_headers!r}; body: {response_payload!r}'
            .format(
                method=method,
                endpoint=endpoint,
                data=data,
                code=response.status_code,
                response_headers=response.headers,
                response_payload=response_payload
            )
        )

        message = {
            'timestamp': timestamp,
            'uid': uid,
            'endpoint': endpoint,
            'method': method,
            'request_data': data,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response_payload,
        }
        self.report(message)
