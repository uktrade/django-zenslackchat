"""
Useful code to aid the main message handler.

Oisin Mulvihill
2020-08-18

"""
import os
import pprint
import logging

from slack.errors import SlackApiError


def config():
    """Recover the slack configuration from the environment.

    The SLACK_BOT_USER_TOKEN must be set or ValueError will be raised.

    """
    token = os.environ.get("SLACK_BOT_USER_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Required environment variable not set: SLACK_BOT_USER_TOKEN "
        )

    return dict(
        token=token
    )

def message_url(channel, message_id):
    """Return a direct link to the message that can be stored in zendesk.

    This expects the environment variable SLACK_WORKSPACE_URI to be set. 

    """
    SLACK_WORKSPACE_URI = os.environ.get(
        'SLACK_WORKSPACE_URI', 
        'https://slack.example.com/archives'
    )

    # Convert to the ID slack uses on the web.
    # e.g. 1597844917.045900 -> p1597844917045900
    msg_id = 'p{}'.format(message_id.replace('.', ''))

    # handle trailing slash being there or not (urljoin doesn't).
    return '/'.join([SLACK_WORKSPACE_URI.rstrip('/'), channel, msg_id])


def post_message(client, chat_id, channel_id, message):
    """Send a message to the parent thread with an update.

    This is also a handy function to aid mocking in tests.

    """
    log = logging.getLogger(__name__)

    log.debug(
        f"chat_id:<{chat_id}> channel:<{channel_id}> message:<{message}>"
    )

    return client.chat_postMessage(
        channel=channel_id,
        text=message,
        thread_ts=chat_id
    )


