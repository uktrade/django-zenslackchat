"""
Useful code to aid the main message handler.

Oisin Mulvihill
2020-08-18

"""
import os
import logging


def message_url(workspace_uri, channel, message_id):
    """Return a direct link to the message that can be stored in zendesk.

    """
    # Convert to the ID slack uses on the web.
    # e.g. 1597844917.045900 -> p1597844917045900
    msg_id = 'p{}'.format(message_id.replace('.', ''))

    # handle trailing slash being there or not (urljoin doesn't).
    return '/'.join([workspace_uri.rstrip('/'), channel, msg_id])


def post_message(client, chat_id, channel_id, message):
    """Send a message to the parent thread with an update.

    :param client: The Slack web client to use.

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


