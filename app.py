#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import quart.flask_patch
from quart import jsonify, request, Quart, websocket

from flask_sqlalchemy import SQLAlchemy

app = Quart(__name__)
app.config.update({
    'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL') or 'sqlite:///:memory:',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
})
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '<User %r>' % self.username

    def to_dict(self):
        return {'username':self.username, 'email':self.email}

# Sample main page
@app.route('/')
async def home():
    return 'Hello, World!'

# Sample main page
@app.route('/users', methods=['GET', 'POST'])
async def users():
    if request.method == 'GET':
        return jsonify([user.to_dict() for user in User.query.all()])
    data = await request.get_json()
    user = User(username=data.get('username'), email=data.get('email'))
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict())

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
