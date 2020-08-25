"""
"""
import json
import pprint
import logging

from flask import Flask
from flask import request
from flask import Response
from flask import current_app, Blueprint, render_template

from zenslackchat import message
from zenslackchat import botlogging

app = Blueprint('app', __name__)


@app.route('/zendesk/webhook/comment', methods=['POST'])
def zendesk_webhook():
    """Handle the comment trigger event we have been POSTed.

    Recover and update the comments with lastest from Zendesk

    """
    log = logging.getLogger(__name__)

    headers = pprint.pformat(dict(request.headers))
    log.debug(f"Headers:\n{headers}")

    # args = pprint.pformat(dict(request.args))
    # log.debug(f"Query:\n{args}")

    raw_data = request.get_data()        
    log.debug(f'Raw POSTed data:\n{raw_data}')

    # This will handle regardless or errors and return without error 
    # to zendesk. 
    message.update_comments_from_zendesk(raw_data)

    return Response("Received OK, Thanks.")


@app.route('/')
def index():
    """Default site root."""
    return Response("Hello.")


def create_app():
    """Create the flask app hooking up the 
    """
    botlogging.log_setup()

    main_app = Flask(__name__)
    main_app.url_map.strict_slashes = False
    main_app.register_blueprint(app)

    return main_app