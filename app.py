#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps
import os

from flask import (
    abort,
    current_app,
    Flask,
    jsonify,
    request,
)
from twilio.request_validator import RequestValidator
try:
    from twilio.twiml import Response
except ImportError:
    from twilio.twiml.messaging_response import MessagingResponse as Response

app = Flask(__name__)

def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid (or if DEBUG is True)
        # and return a 403 error if it's not
        if request_valid or current_app.debug:
            return f(*args, **kwargs)
        return abort(403)
    return decorated_function

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

@app.route('/voice/', methods=['POST'], strict_slashes=False)
@validate_twilio_request
def incoming_call():
    """Twilio Voice URL - receives incoming calls from Twilio"""

    # Create a new TwiML response
    resp = Response()

    # <Say> a message to the caller
    from_number = request.values['From']
    body = """
    Thanks for calling!

    Your phone number is {0}. I got your call because of Twilio's webhook.

    Goodbye!""".format(' '.join(from_number))
    resp.say(body)

    # Return the TwiML
    return str(resp)

@app.route('/message/', methods=['POST'], strict_slashes=False)
@validate_twilio_request
def incoming_message():
    """Twilio Messaging URL - Respond to incoming messages from Twilio with a simple text message"""

    # Create a new TwiML response
    resp = Response()

    # <Message> a text back to the person who texted us
    msg = resp.message()

    # retrieve incoming message from POST request
    incoming_msg = request.POST['Body']

    msg.body(f"Your text to me was {incoming_msg} characters long. Webhooks are neat :)")
    msg.media('https://twilio-cms-prod.s3.amazonaws.com/images/twilio-logo-red.width-640.png')

    # Return the TwiML
    return resp.to_xml()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
