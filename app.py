#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import Flask, jsonify, request

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
