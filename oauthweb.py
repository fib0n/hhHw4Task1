from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url

import requests
import requests.auth

CLIENT_ID = 'e2WGhRK0danWZg'
CLIENT_SECRET = 'NA9Chz_TJwJnfRlL1MyJateyg2s'
PORT = 8082
REDIRECT_URI = 'http://localhost:%d/oAuth_callback' % PORT
API_URL = 'https://ssl.reddit.com/api/v1/'

STATES = set()


def get_auth_url():
    import os
    import binascii

    state = binascii.b2a_hex(os.urandom(7))
    STATES.add(state)

    params = {'client_id': CLIENT_ID,
              'response_type': 'code',
              'state': state,
              'redirect_uri': REDIRECT_URI,
              'duration': 'temporary',
              'scope': 'identity'}
    import urllib

    return API_URL + 'authorize?' + urllib.urlencode(params)


def get_token_response_json(code):
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {'grant_type': 'authorization_code', 'code': code,
                 'redirect_uri': REDIRECT_URI}
    response = requests.post(API_URL + 'access_token',
                             auth=client_auth, data=post_data)
    json = response.json()
    return json


def get_info(token):
    headers = {'Authorization': 'bearer ' + token, 'User-Agent': 'requests by fib0n'}
    response = requests.get('https://oauth.reddit.com/api/v1/me',
                            headers=headers)
    return response.json()


class IndexHandler(RequestHandler):
    def get(self):
        self.write(get_auth_url())

    def data_received(self, chunk):
        pass


class OAuthCallbackHandler(RequestHandler):
    def get(self):
        error = self.get_argument('error', None)
        if error:
            self.clear()
            self.finish('Error: ' + error)

        state = self.get_argument('state')
        if state not in STATES:
            self.clear()
            self.set_status(403, 'state %s is not exists' % state)
            return

        STATES.remove(state)
        code = self.get_argument('code')
        if not code:
            self.clear()
            self.set_status(500, 'code is empty')
            return

        token_response_json = get_token_response_json(code)
        if 'error' in token_response_json or 'access_token' not in token_response_json:
            self.clear()
            self.set_status(500, 'Could not get access_token. ' + token_response_json)
            return

        token = token_response_json['access_token']
        print 'Token: ', token

        self.write(get_info(token))

    def data_received(self, chunk):
        pass


def make_app():
    return Application([
        url(r"/", IndexHandler),
        url(r"/oAuth_callback", OAuthCallbackHandler)
    ])


def main():
    app = make_app()
    app.listen(8082)
    IOLoop.current().start()


main()
