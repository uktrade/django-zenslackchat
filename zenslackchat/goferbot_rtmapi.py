#
# Based on article from:
# 
#  https://medium.com/@rdcolema7/
#      building-a-python-slackbot-that-actually-works-2930663e20f3
#
#
import os
import sys
import pprint
import logging
from urllib.parse import urljoin

from slack import RTMClient
from slack.errors import SlackApiError
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import Comment


WORKSPACE_URI  = os.environ.get(
    'WORKSPACE_URI', 'https://ditdigitalteam.slack.com/archives/'
)
EMAIL = os.environ.get('ZENDESK_EMAIL', '<email@example.com>')
TOKEN = os.environ.get('ZENDESK_TOKEN', '<token>')
SUBDOMAIN = os.environ.get('ZENDESK_SUBDOMAIN', '<something>')


def log(message):
    """Convert to proper logging, whos output is being eaten by thread running
    handle message. Odly print to stdout still works. 
    """
    print(message)


def has_ticket(chat_id):
    """Check if the slack parent message is known about
    """
    zenpy_client = Zenpy(
        email=EMAIL,
        token=TOKEN,
        subdomain=SUBDOMAIN,
    )

    for result in zenpy_client.search(chat_id, type='ticket'):
        import ipdb; ipdb.set_trace()

    return False


def create_ticket(chat_id, recipient_email, subject, slack_message_url):
    """Create a new zendesk ticket in response to a new user question.
    """    
    zenpy_client = Zenpy(
        email=EMAIL,
        token=TOKEN,
        subdomain=SUBDOMAIN,
    )

    requestor = zenpy_client.users.me()

    issue = Ticket(
        type='question', 
        external_id=chat_id,
        subject=subject, 
        recipient=recipient_email,
        requestor_id=requestor.id,
    )
    ticket_audit = zenpy_client.tickets.create(issue)

    return ticket_audit


def slack_message_url(channel, message_id):
    """Return the link that can be stored in zendesk."""
    return urljoin(WORKSPACE_URI, channel, message_id)


def message_handler(payload):
    """Decided what to do with the message we have received.
    """
    p = pprint.pformat(payload)
    log(f'Payload:\n{p}\n')

    web_client = payload['web_client']

    data = {}
    channel_id = '?'
    if 'data' in payload:
        data = payload['data']
        channel_id = data['channel']

    text = ''
    if 'text' in data:
        text = data['text']

    if 'bot_id' in data:
        # This is usually us/a bot posting a reply to a message or thread. 
        # Without this we would end up in a loop replying to ourself.
        log(f"Ignoring bot <{data['bot_id']}> message: {text}")
        return

    subtype = ''
    if 'subtype' in data:
        subtype = data['subtype']

    message = {}
    if 'message' in data:
        message = data['message']

    # ID for parent message.
    thread_parent = data.get('ts', '')

    # ID for message under parent.
    thread_ts = data.get('thread_ts', '')

    # Recover the slack channel message author's email address. I assume this
    # is always set on all accounts.
    user_id = data.get('user', '')
    log(f"Recovering profile for user <{user_id}>")
    resp = web_client.users_info(user_id)
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
        log(f"Received message from '{recipient_email}': {text}\n")

        # Zendesk ID I can set. I'll use the parent conversation as the ID
        # and tie the ticket back to this. I'll use Zendesk as the 
        # "backend" store.
        chat_id = thread_parent

        # New issue: generate Zendesk ticket
        slack_chat_url = slack_message_url(channel_id, thread_parent)

        if not has_ticket(chat_id):
            # No clear to create.
            response = create_ticket(
                chat_id=chat_id, 
                recipient_email=recipient_email, 
                subject=text, 
                slack_message_url=slack_chat_url,
            )

            # Once-off response to parent thread:
            message = "Hello, your new support request is <Zendesk Link>"

            try:
                response = web_client.chat_postMessage(
                    channel=channel_id,
                    text=message,
                    thread_ts=thread_parent if thread_parent else thread_ts
                )

            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["ok"] is False
                # str like 'invalid_auth', 'channel_not_found'
                assert e.response["error"]  
                log(f"Got an error: {e.response['error']}")

            else:
                log(f"Response to postMessage: {response}")

        else:
            log(f"The issue '{text}' is already in Zendesk '{chat_id}'")


@RTMClient.run_on(event='message')
def react_to(**payload):
    """Pass the payload on to the message handler.

    This use catch-all try-except to catch exceptions and log them. Without 
    this they are hidden from you. You see nothing happening. At least with
    try-except I can see what went wrong.

    """
    try:
        message_handler(payload)
    except:
        logging.exception("Message Handler Fail: ")


def main():
    RTMClient(token=os.environ["SLACKBOT_API_TOKEN"]).start()
    logging.warning(f"Slackbot exit.")
    sys.exit(0)


if __name__ == "__main__":
    main()

    