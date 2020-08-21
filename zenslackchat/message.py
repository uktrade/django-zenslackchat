"""
The main bot message handler.

This determines how to react to messages we receive from slack over the 
real time messaging (RTM) API.

Oisin Mulvihill
2020-08-20

"""
import logging

import zenpy

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

    # The docs https://api.slack.com/rtm for RTM API say a message should have
    # 'type = messsage' field. Using the slack client RTM however shows this is
    # not the case. I have noticed all other messages have a subtype. So I'm
    # just going to ignore all of these and see how I get on. I can manage the
    # message / message-reply based on the ts/thread_ts fields and whether they
    # are populated or not. I'm calling ts: chat_id and thread_ts: thread_id.
    #
    subtype = data.get('subtype')
    if subtype:
        log.debug(f"Ignoring subtype '{subtype}': {text}\n")
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
                url = zendesk_ticket_url(ticket.id)
                try:
                    close_ticket(thread_id)
                except zenpy.lib.exception.APIException:
                    post_message(
                        web_client, thread_id, channel_id, 
                        f'🤖 Ticket {url} is already closed.'
                    )
                else:
                    post_message(
                        web_client, thread_id, channel_id, 
                        f'🤖 Understood. Ticket {url} has been closed.'
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