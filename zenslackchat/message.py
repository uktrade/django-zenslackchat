"""
The main bot message handler.

This determines how to react to messages we receive from slack over the 
real time messaging (RTM) API.

Oisin Mulvihill
2020-08-20

"""
import logging

from zenslackchat.zendesk_api import get_ticket
from zenslackchat.zendesk_api import close_ticket
from zenslackchat.zendesk_api import create_ticket
from zenslackchat.zendesk_api import zendesk_ticket_url
from zenslackchat.slack_utils import message_url
from zenslackchat.slack_utils import post_message


def handler(payload):
    """Decided what to do with the message we have received.
    
    :returns: True or False.

    False means the message was ignored as its not one we handle.

    """
    log = logging.getLogger(__name__)

    # Fields that must be present for this to work:
    web_client = payload['web_client']
    data = payload['data']
    channel_id = data['channel']
    text = data.get('text', '')

    subtype = data.get('subtype')
    if subtype in ['bot_message', 'message_changed', 'message_deleted']:
        # Deleted messages I don't think I care about. Messages deleted inside
        # a thread show up as changed. Again I'm not sure I care it might be 
        # more work than its worth to keep up with these.
        log.debug(f"Ignoring subtype '{subtype}': {text}\n")
        return False

    elif subtype == "message_replied":
        # ignore this too. We recieve the parent message first. The next 
        # message is then the actual reply. I can manage which is which based
        # on the on what I call the chat_id and thread_id.
        return False

    # A message
    user_id = data['user']
    chat_id = data['ts']
    # won't be present in a new top-level message we will reply too
    thread_id = data.get('thread_ts', '')

    # Recover the slack channel message author's email address. I assume 
    # this is always set on all accounts.
    log.debug(f"Recovering profile for user <{user_id}>")
    resp = web_client.users_info(user=user_id)
    recipient_email = resp.data['user']['profile']['email']

    # Get any existing ticket from zendesk:
    if chat_id and thread_id:
        # This is a reply message, use the thread_id to recover from zendesk:
        slack_chat_url = message_url(channel_id, thread_id)
        ticket = get_ticket(thread_id)
        log.debug(
            f"Received thread message from '{recipient_email}': {text}\n"
        )
        if ticket:
            # Handle thread commands here e.g. done/reopen
            log.debug(
                f'Recoverd ticket {ticket.id} from slack {slack_chat_url}'
            )
            command = text.strip().lower()
            if command == 'done':
                # Time to close the ticket as the issue has been resolved.
                log.debug(
                    f'Closing ticket {ticket.id} from slack {slack_chat_url}.'
                )
                close_ticket(chat_id)
                post_message(
                    web_client, chat_id, channel_id, 
                    '🤖 Understood. The ticket has been closed.'
                )

        else:
            # This could be an old thread pre-bot days:
            log.warn(
                f'No ticket found in slack {slack_chat_url}. Old thread?'
            )

    else:
        slack_chat_url = message_url(channel_id, chat_id)
        ticket = get_ticket(chat_id)
        # New issue?
        if not ticket:
            # Yes, new ticket time.
            log.debug(
                f"Received message from '{recipient_email}': {text}\n"
            )
            ticket = create_ticket(
                chat_id=chat_id, 
                recipient_email=recipient_email, 
                subject=text, 
                slack_message_url=slack_chat_url,
            )
            # Once-off response to parent thread:
            url = zendesk_ticket_url(ticket.id)
            message = f"Hello, your new support request is {url}"
            post_message(web_client, chat_id, channel_id, message)

        else:
            # No, we have a ticket already for this.
            log.info(
                f"The issue '{text}' is already in Zendesk '{chat_id}'"
            )

    return True