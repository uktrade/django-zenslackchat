"""
Useful code to aid the main message handler.

To simplify testing I keep these functions django free and pass in whats needed 
in arguments. This can then be easily faked/mocked.

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


def url_to_chat_id(slack_url):
    """Convert a copy-n-pasted slack chat URL to the chat_id

    Go from: https://xyz.slack.com/archives/.../p1614771038052300

    To: 1614771038.052300
    
    """
    # Recover the last element in URL and convert to chat_id
    chat_id = (slack_url.split('/')[-1]).lower().strip()

    # convert to chat_id stripping the trailing p
    chat_id = chat_id[1:] if chat_id[0] == 'p' else chat_id

    # convert to timestamp with:
    chat_id = f"{chat_id[:-6]}.{chat_id[-6:]}"
    
    return chat_id


def create_thread(client, channel_id, message):
    """Create a parent message which will be the thread for further comms.

    :param client: The Slack web client to use.

    :param channel_id: The slack support chanel ID.

    :param message: The top level message.

    :returns: The chat_id of the new parent message.

    """
    log = logging.getLogger(__name__)

    log.debug(f"channel:<{channel_id}> message:<{message}>")
    response = client.chat_postMessage(
        channel=channel_id,
        text=message,
    )

    chat_id = response['message']['ts']
    log.debug(f"New message chat_id:<{chat_id}>")

    return chat_id


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
