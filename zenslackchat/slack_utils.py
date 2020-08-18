"""
Code to help me work with slack messaging.

Oisin Mulvihill
2020-08-18

"""
import os
import pprint
import logging

from slack.errors import SlackApiError

from zenslackchat import zendesk_api


def config():
    """Recover the slack configuration from the environment.

    The SLACKBOT_API_TOKEN must be set or ValueError will be raised.

    """
    token = os.environ.get("SLACKBOT_API_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Required environment variable not set: SLACKBOT_API_TOKEN "
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

    # handle trailing slash being there or not (urljoin doesn't).
    return '/'.join([SLACK_WORKSPACE_URI.rstrip('/'), channel, message_id])


def post_message(client, chat_id, channel_id, message):
    """Send a message to the parent thread with an update.

    This is also a handy function to aid mocking in tests.

    """
    return client.chat_postMessage(
        channel=channel_id,
        text=message,
        thread_ts=chat_id
    )


def message_handler(payload):
    """Decided what to do with the message we have received.
    """
    p = pprint.pformat(payload)
    logging.debug(f'Payload received:\n{p}\n')

    # Fields that must be present for this to work:
    web_client = payload['web_client']
    data = payload['data']
    channel_id = data['channel']

    text = data.get('text')
    if 'bot_id' in data:
        # This is usually us/a bot posting a reply to a message or thread. 
        # Without this we would end up in a loop replying to ourself.
        logging.debug(f"Ignoring bot <{data['bot_id']}> message: {text}")
        return

    user_id = None
    if 'message' in data:
        # reply
        text = data['message']['text']
        user_id = data['message']['user']

    else:
        text = data['text']
        user_id = data.get('user')

    # ID for parent message (thread_ts is ID for message under the parent)
    chat_id = data.get('ts', '')

    subtype = ''
    if 'subtype' in data:
        subtype = data['subtype']
        
    if user_id:
        # Recover the slack channel message author's email address. I assume 
        # this is always set on all accounts.
        logging.debug(f"Recovering profile for user <{user_id}>")
        resp = web_client.users_info(user=user_id)
        recipient_email = resp.data['user']['profile']['email']

    if subtype == 'message_replied':
        # Do anything here? 
        #
        # Yes, I need to look out for 'done' to indicate the issue should be
        # closed. Possible look out for 'reopen' to undo mistaken 'done' or if
        # the issue was not actually fixed.
        # 
        # I could check the conversation is synchronised. However I suspect 
        # I'll need to implements webhooks or something to get updates on an 
        # issue from Zendesk. Will need to research.
        #
        pass

    else:
        logging.debug(f"Received message from '{recipient_email}': {text}\n")

        # I'll use the parent conversation as the ID and tie the ticket back to 
        # this. I'll use Zendesk as the "backend" store.

        # New issue: generate Zendesk ticket
        slack_chat_url = message_url(channel_id, chat_id)

        if not zendesk_api.get_ticket(chat_id):
            # No clear to create.
            ticket = zendesk_api.create_ticket(
                chat_id=chat_id, 
                recipient_email=recipient_email, 
                subject=text, 
                slack_message_url=slack_chat_url,
            )
            # Once-off response to parent thread:
            url = zendesk_api.zendesk_ticket_url(ticket.id)
            message = f"Hello, your new support request is {url}"
            post_message(web_client, chat_id, channel_id, message)

        else:
            logging.info(
                f"The issue '{text}' is already in Zendesk '{chat_id}'"
            )