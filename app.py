#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import Flask, jsonify, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Sample main page
@app.route('/')
@app.route('/<name>')
def home(name=None):
	return f'Hello, {name or "World"}!'

@app.route('/query', methods=['GET'])
def query_string():
	name = request.args.get('name') or 'Guest'
	return f'Hello, {name}!'

# Sample setup script
@app.route('/setup/', strict_slashes=False)
def setup_route():
    data = {
        'worked': True,
        'msg': 'It worked!'
    }
    return jsonify(data)

@app.route('/sms/', methods=['POST'], strict_slashes=False)
def sms_reply():
    """Respond to incoming calls with a simple text message."""

    msg = request.form.get('Body')

    resp = MessagingResponse()
    resp.message(f'You said: {msg}')

    return resp.to_xml()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
