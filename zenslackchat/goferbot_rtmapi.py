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


SLACK_WORKSPACE_URI = os.environ.get(
    'SLACK_WORKSPACE_URI', 
    'https://ditdigitalteam.slack.com/archives/'
)
ZENDESK_TICKET_URI = os.environ.get(
    'ZENDESK_TICKET_URI', 
    'https://ditstaging.zendesk.com/agent/tickets'
)



def slack_message_url(channel, message_id):
    """Return the link that can be stored in zendesk."""
    return urljoin(SLACK_WORKSPACE_URI, channel, message_id)


def zendesk_ticket_url(channel, message_id):
    """Return the link that can be stored in zendesk."""
    return urljoin(ZENDESK_TICKET_URI, channel, message_id)


def log(message):
    """Convert to proper logging, whos output is being eaten by thread running
    handle message. Odly print to stdout still works. 
    """
    print(message)


def zapi():
    """Returns a configured Zenpy client instance ready for use.

    This expects the environment to be set:

        - ZENDESK_EMAIL
        - ZENDESK_TOKEN
        - ZENDESK_SUBDOMAIN

    This currently uses the Token based Zendesk API key. We need to move to
    OAuth based system for more granular access to just what is needed.

    """
    EMAIL = os.environ.get('ZENDESK_EMAIL', '<email@example.com>')
    TOKEN = os.environ.get('ZENDESK_TOKEN', '<token>')
    SUBDOMAIN = os.environ.get('ZENDESK_SUBDOMAIN', '<something>')

    return Zenpy(
        email=EMAIL,
        token=TOKEN,
        subdomain=SUBDOMAIN,
    )

def get_ticket(chat_id):
    """Recover the zendesk ticket for a given slack parent message.

    :param chat_id: The 'ts' payload used by slack to identify a message.

    :returns: A Zenpy.Ticket instance or None if nothing was found.

    """
    returned = False


    # There should only be one so 
    results = [item for item in zenpy_client.search(chat_id, type='ticket')]
    if results > 0:
        returned = True

    return returned


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
        description=subject, 
        recipient=recipient_email,
        requestor_id=requestor.id,
    )
    ticket_audit = zenpy_client.tickets.create(issue)

    return ticket_audit


def message_handler(payload):
    """Decided what to do with the message we have received.
    """
    p = pprint.pformat(payload)
    log(f'Payload:\n{p}\n')

    # Fields that must be present for this to work:
    web_client = payload['web_client']
    data = payload['data']
    channel_id = data['channel']

    text = data.get('text')
    if 'bot_id' in data:
        # This is usually us/a bot posting a reply to a message or thread. 
        # Without this we would end up in a loop replying to ourself.
        log(f"Ignoring bot <{data['bot_id']}> message: {text}")
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
        log(f"Recovering profile for user <{user_id}>")
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
        log(f"Received message from '{recipient_email}': {text}\n")

        # I'll use the parent conversation as the ID and tie the ticket back to 
        # this. I'll use Zendesk as the "backend" store.

        # New issue: generate Zendesk ticket
        slack_chat_url = slack_message_url(channel_id, chat_id)

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
                    thread_ts=chat_id
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

    