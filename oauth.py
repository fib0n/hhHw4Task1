#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import datetime
import cPickle

import requests
import requests.auth


def ssl(event_type, post_data):
    client_id = 'CVd7f9CbGe7SlQ'
    client_secret = 'sYcvKaEZEk7vZjhz3qzlOD9Jl0s'
    client_auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    response = requests.post('https://ssl.reddit.com/api/v1/'
                             + event_type, auth=client_auth,
                             data=post_data)
    return response.json()


def get_token_response_json(username, password):
    post_data = {'grant_type': 'password', 'username': username,
                 'password': password}
    json = ssl('access_token', post_data)
    if 'access_token' in json:
        return json
    raise Exception('could not get access_token', json)


def get_info(token):
    headers = {'Authorization': 'bearer ' + token,
               'User-Agent': 'requests by fib0n'}
    response = requests.get('https://oauth.reddit.com/api/v1/me',
                            headers=headers)
    return response.json()

# чтобы каждый раз не запрашивать токен, который валиден 1 час для реддита,
# сохраняю его в файл <username>.pkl


def get_token_from_file(filename):
    try:
        if not os.path.isfile(filename):
            return

        with open(filename, 'rb') as data_file:
            data = cPickle.load(data_file)
            if 'expired' not in data:
                return
            if int(datetime.datetime.now().strftime('%s')) >= int(data['expired']):
                return
            return data['token']
    except:
        pass


def save_token(filename, data):
    try:
        with open(filename, 'wb') as data_file:
            cPickle.dump(data, data_file, cPickle.HIGHEST_PROTOCOL)
    except:
        pass


def manager(username, password):
    filename = username + '.pkl'
    token = get_token_from_file(filename)
    try:
        if not token:
            json = get_token_response_json(username, password)
            token = json['access_token']
            expired_seconds = int(datetime.datetime.now().strftime('%s')) + int(json['expires_in'])
            token_data = {'token': token, 'expired': expired_seconds}
            save_token(filename, token_data)

        print 'Token: ', token
        print 'Your info: ', get_info(token)
    except Exception, ex:
        print ex

manager(sys.argv[1], sys.argv[2])
