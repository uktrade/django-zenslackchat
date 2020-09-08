"""
The main bot message handler.

This determines how to react to messages we receive from slack over the 
real time messaging (RTM) API.

Oisin Mulvihill
2020-08-20

"""
import os
import json
import time
import logging
import datetime
from time import mktime

import zenpy
from slack import WebClient
from dateutil.parser import parse

from zenslackchat.zendesk_api import api
from zenslackchat.zendesk_api import get_ticket
from zenslackchat.zendesk_api import add_comment
from zenslackchat.zendesk_api import close_ticket
from zenslackchat.zendesk_api import create_ticket
from zenslackchat.zendesk_api import zendesk_ticket_url
from zenslackchat.slack_utils import message_url
from zenslackchat.slack_utils import post_message
from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError


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

    # I'm ignoring all bot messages. I can manage the message / message-reply 
    # based on the ts/thread_ts fields and whether they are populated or not. 
    # I'm calling 'ts' chat_id and 'thread_ts' thread_id.
    #
    subtype = data.get('subtype')
    if subtype == 'bot_message' or 'bot_id' in data:
        log.debug(f"Ignoring bot message: {text}\n")
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
    print(f"resp.data:\n{resp.data}\n")
    #recipient_email = resp.data['user']['profile']['email']
    recipient_email = resp.data['user']['real_name']

    # zendesk ticket instance
    ticket = None

    # Get any existing ticket from zendesk:
    if chat_id and thread_id:
        log.debug(
            f"Received thread message from '{recipient_email}': {text}\n"
        )

        # This is a reply message, use the thread_id to recover from zendesk:
        slack_chat_url = message_url(channel_id, thread_id)
        try:
            issue = ZenSlackChat.get(channel_id, thread_id)

        except NotFoundError:
            # This could be an thread that happened before the bot was running:
            log.warn(
                f'No ticket found in slack {slack_chat_url}. Old thread?'
            )

        else:
            ticket_id = issue.ticket_id

            # Handle thread commands here e.g. done/reopen
            log.debug(
                f'Recoverd ticket {ticket_id} from slack {slack_chat_url}'
            )
            command = text.strip().lower()
            if command == 'resolve ticket':
                # Time to close the ticket as the issue has been resolved.
                log.debug(
                    f'Closing ticket {ticket_id} from slack {slack_chat_url}.'
                )
                url = zendesk_ticket_url(ticket_id)
                ZenSlackChat.resolve(channel_id, chat_id)
                try:
                    close_ticket(issue)
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

            # Add comment to Zendesk:
            ticket = get_ticket(ticket_id)
            add_comment(ticket, text)

    else:
        slack_chat_url = message_url(channel_id, chat_id)
        try:
            issue = ZenSlackChat.get(channel_id, chat_id)

        except NotFoundError:
            # No issue found. It looks like its new issue:
            log.debug(
                f"Received message from '{recipient_email}': {text}\n"
            )
            ticket = create_ticket(
                external_id=chat_id, 
                recipient_email=recipient_email, 
                subject=text, 
                slack_message_url=slack_chat_url,
            )

            # Store all the details in our DB:
            ZenSlackChat.open(channel_id, chat_id, ticket_id=ticket.id)

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


def ts_to_datetime(epoch):
    """Convert raw UTC slack message epoch times to datetime.

    :param epoch: 1598459584.013100

    :returns: datetime.datetime(2020, 8, 26, 17, 33, 4)

    """
    dt = datetime.datetime.fromtimestamp(mktime(time.localtime(epoch)))
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def update_with_comments_from_zendesk(event):
    """Handle the raw data from a Zendesk webhook and return without error.

    This will log all exceptions rather than cause zendesk reject 
    our endpoint.

    """
    log = logging.getLogger(__name__)
    
    chat_id = event['external_id']
    ticket_id = event['ticket_id']

    log.debug(f'Recovering ticket by its Zendesk ID:<{ticket_id}>')
    issue = ZenSlackChat.get_by_ticket(chat_id, ticket_id)
    if not issue:
        log.debug(
            f'No Ticket Found for Zendesk ID {ticket_id}.'
        )
        return

    zendesk_client = api()
    slack_client = WebClient(token=os.environ['SLACKBOT_API_TOKEN'])

    # Recover the conversation for this channel and chat_id
    resp = slack_client.conversations_replies(
        channel=issue.channel_id, ts=chat_id
    )

    messages = resp.data['messages']
    latest_reply = None
    if len(messages) > 1:
        parent = messages[0]
        latest_reply = ts_to_datetime(parent['latest_reply'])
    
    for comment in zendesk_client.tickets.comments(ticket=ticket_id):
        created_at = parse(comment['created_at'])

        import ipdb; ipdb.set_trace()


