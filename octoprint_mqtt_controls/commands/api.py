import requests

from urlparse import urljoin

from .base import CommandBase

RESPONSE_SUBTOPIC = 'control-response/'


class APIRequestCommand(CommandBase):
    subtopic = 'mqtt-rest-api/'
    report_subtopic = 'control-response/'

    def __init__(self, *args, **kwargs):
        super(APIRequestCommand, self).__init__(*args, **kwargs)
        self.api_session = self._create_api_session(
            self.plugin_instance.api_key
        )
        self.api_url_base = self.plugin_instance.api_url_base

    def _create_api_session(self, api_key):
        s = requests.Session()
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['X-Api-Key'] = api_key
        s.headers.update(headers)
        return s

    def _get_url(self, endpoint):
        return urljoin(self.api_url_base, endpoint)

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
            self._get_url(endpoint),
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
