# coding=utf-8
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

    headers = {'User-Agent': 'requests by fib0n'}
    response = requests.post(API_URL + 'access_token',
                             auth=client_auth, data=post_data,
                             headers=headers)
    json = response.json()
    return json


def get_info(token):
    headers = {'Authorization': 'bearer ' + token, 'User-Agent': 'requests by fib0n'}
    response = requests.get('https://oauth.reddit.com/api/v1/me',
                            headers=headers)
    return response.json()


class IndexHandler(RequestHandler):
    def get(self):
        self.write('<a href="%s">Войти через reddit</a>' % get_auth_url())

    def data_received(self, chunk):
        pass


class OAuthCallbackHandler(RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.clear()
        message = kwargs.get('message', 'Internal server error')
        self.set_status(status_code, message)
        self.write(message)

    def get(self):
        error = self.get_argument('error', None)
        if error:
            self.write_error(500, message='Error: ' + error)
            return

        state = self.get_argument('state', None)
        if state not in STATES:
            self.write_error(403, message='State "%s" is not exists' % state)
            return

        STATES.remove(state)
        code = self.get_argument('code', None)
        if not code:
            self.write_error(500, message='Code is empty')
            return

        json = get_token_response_json(code)
        if 'error' in json or 'access_token' not in json:
            self.write_error(500,
                             message="Couldn't get token. Response: " + str(json))
            return

        token = json['access_token']
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
