from __future__ import absolute_import

from requests.exceptions import HTTPError
from sentry.http import build_session

from sentry_plugins.exceptions import ApiError


class PushsaferClient(object):
    base_url = 'https://www.pushsafer.com'

    def __init__(self, privatekey=None):
        self.privatekey = privatekey

    def request(self, method, path, data):
        payload = {
            'k': self.privatekey,
        }
        payload.update(data)

        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='{}{}'.format(self.base_url, path),
                data=payload,
                allow_redirects=True,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def send_message(self, data):
        return self.request('POST', '/api', data)
