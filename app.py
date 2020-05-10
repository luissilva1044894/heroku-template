#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from quart import jsonify, request, Quart, websocket

app = Quart(__name__)

# Sample main page
@app.route('/')
async def home():
	return 'Hello, World!'

@app.route('/query', methods=['GET'])
async def query_string():
	name = request.args.get('name') or 'Guest'
	return f'Hello, {name}!'

# Sample setup script
@app.route('/setup/', strict_slashes=False)
async def setup_route():
    data = {
        'worked': True,
        'msg': 'It worked!'
    }
    return jsonify(data)

@app.websocket('/ws')
async def ws():
    while True:
        await websocket.send('Hello!')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
