#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from flask import Flask, jsonify, render_template

app = Flask(__name__, static_folder='static', template_folder='templates', static_url_path='')

@app.context_processor
def utility_processor():
    return { 'current_year': datetime.utcnow().year }

# Sample main page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/<name>', methods=['GET'])
def hello_someone(name):
    return render_template('index.html', name=name.title())

@app.route('/hello')
def hello():
    return 'Hello, World!'

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
