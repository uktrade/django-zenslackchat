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
import pprint
import logging
import datetime
from time import mktime
from operator import itemgetter

import zenpy

from dateutil.parser import parse

from webapp import settings
from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError
from zenslackchat.slack_api import message_url
from zenslackchat.slack_api import post_message
from zenslackchat.zendesk_api import get_ticket
from zenslackchat.zendesk_api import add_comment
from zenslackchat.zendesk_api import close_ticket
from zenslackchat.zendesk_api import create_ticket
from zenslackchat.zendesk_api import zendesk_ticket_url


IGNORED_SUBTYPES = [
    'channel_join', 'bot_message', 'channel_rename', 'message_changed', 
    'message_deleted'    
]


def handler(event, our_channel, slack_client, zendesk_client, workspace_uri):
    """Decided what to do with the message we have received.

    :param event: The slack event received.

    :param our_channel: The slack channel id we listen to.

    All other events on different channels are silently ignored.

    :param slack_client: The slack web client instance.

    :param zendesk_client: The Zendesk web client instance.

    :param workspace_uri: The link to slack workspace archives.

    :returns: True or False.

    False means the message was ignored as its not one we handle.

    """
    log = logging.getLogger(__name__)

    channel_id = event.get('channel', "").strip()
    text = event.get('text', '')

    if channel_id != our_channel:
        if settings.DEBUG:
            log.debug(
                f"Ignoring event from channel id:<{channel_id} as its not from"
                f"our support channel id:{our_channel}"
            )
        return False
    
    else:
        log.debug(f"New message on support channel<{channel_id}>: {text}")

    # I'm ignoring all bot messages. I can manage the message / message-reply 
    # based on the ts/thread_ts fields and whether they are populated or not. 
    # I'm calling 'ts' chat_id and 'thread_ts' thread_id.
    subtype = event.get('subtype')
    if subtype == 'bot_message' or 'bot_id' in event:
        #log.debug(f"Ignoring bot message: {text}")
        return False

    elif subtype in IGNORED_SUBTYPES:
        #log.debug(f"Ignoring subtype we don't handle: {subtype}")
        return False

    # A message
    user_id = event['user']
    chat_id = event['ts']
    # won't be present in a new top-level message we will reply too
    thread_id = event.get('thread_ts', '')

    # Recover the slack channel message author's email address. I assume 
    # this is always set on all accounts.
    log.debug(f"Recovering profile for user <{user_id}>")
    resp = slack_client.users_info(user=user_id)
    # print(f"resp.event:\n{resp.event}\n")
    real_name = resp.data['user']['real_name']
    recipient_email = resp.data['user']['profile']['email']

    # zendesk ticket instance
    ticket = None

    # Get any existing ticket from zendesk:
    if chat_id and thread_id:
        log.debug(
            f"Received thread message from '{recipient_email}': {text}\n"
        )

        # This is a reply message, use the thread_id to recover from zendesk:
        slack_chat_url = message_url(workspace_uri, channel_id, thread_id)
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
                try:
                    close_ticket(zendesk_client, issue)

                except zenpy.lib.exception.APIException:
                    log.exception("Close ticket exception (error?): ")
                    post_message(
                        slack_client, thread_id, channel_id, 
                        f'🤖 Ticket {url} is already closed.'
                    )
                else:
                    ZenSlackChat.resolve(zendesk_client, channel_id, chat_id)
                    post_message(
                        slack_client, thread_id, channel_id, 
                        f'🤖 Understood. Ticket {url} has been closed.'
                    )

            # Add comment to Zendesk:
            try:
                ticket = get_ticket(zendesk_client, ticket_id)

            except zenpy.lib.exception.APIException:
                post_message(
                    slack_client, thread_id, channel_id, 
                    "🤖 I'm unable to send comment to Zendesk (API Error)."
                )
                log.exception("Zendesk API error: ")

            else:
                add_comment(
                    zendesk_client, ticket, f"{real_name} (Slack): {text}"
                )

    else:
        slack_chat_url = message_url(workspace_uri, channel_id, chat_id)
        try:
            issue = ZenSlackChat.get(channel_id, chat_id)

        except NotFoundError:
            # No issue found. It looks like its new issue:
            log.debug(
                f"Received message from '{recipient_email}': {text}\n"
            )
            try:
                ticket = create_ticket(
                    zendesk_client, 
                    external_id=chat_id, 
                    recipient_email=recipient_email, 
                    subject=text, 
                    slack_message_url=slack_chat_url,
                )

            except zenpy.lib.exception.APIException:
                post_message(
                    slack_client, thread_id, channel_id, 
                    "🤖 I'm unable to talk to Zendesk (API Error)."
                )
                log.exception("Zendesk API error: ")

            else:
                # Store all the details in our DB:
                ZenSlackChat.open(channel_id, chat_id, ticket_id=ticket.id)

                # Once-off response to parent thread:
                url = zendesk_ticket_url(ticket.id)
                message = f"Hello, your new support request is {url}"
                post_message(slack_client, chat_id, channel_id, message)

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
    dt = datetime.datetime.fromtimestamp(mktime(time.localtime(float(epoch))))
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def utc_to_datetime(iso8601_str):
    """Convert raw UTC slack message epoch times to datetime.

    :param iso8601_str: '2020-09-08T16:35:14Z'

    An iso8601 string parse can interpret.

    :returns: datetime.datetime(2020, 9, 8, 16, 35, 14, tzinfo=utc)

    """
    dt = parse(iso8601_str)
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def messages_for_slack(slack, zendesk):
    """Work out which messages from zendesk need to be added to the slack 
    conversation.

    :param slack: A list of slack messages.

    :param zendesk: A list of zendesk comment message.

    :returns: An empty list or list of messages to be added.

    """
    log = logging.getLogger(__name__)

    slack = sorted(slack, key=itemgetter('created_at')) 
    msgs = [s['text'] for s in slack]
    log.debug(f"Raw Slack messages:\n{slack}")
    log.debug(f"Slack messages:\n{msgs}")

    zendesk = sorted(zendesk, key=itemgetter('created_at'), reverse=True) 
    msgs = [z['body'] for z in zendesk]
    log.debug(f"Zendesk messages:\n{msgs}")

    # Ignore the first message which is the parent message. Also ignore the 
    # second message which is our "link to zendesk ticket" message.
    lookup = {}
    for msg in slack[2:]:
        # text = msg['text']
        text = msg['text'].split('(Zendesk):')[-1].strip()
        log.debug(f"slack msg to index:{text}")
        lookup[text] = 1
    # log.debug(f"messages to consider from slack:{len(slack)}")
    # log.debug(f"lookup:\n{lookup}")

    # remove api messages which come from slack
    for_slack = []
    for msg in zendesk:
        if msg['via']['channel'] == 'web' and msg['body'] not in lookup:
            log.debug(f"msg to be added:{msg['body']}")
            for_slack.append(msg)
        else:
            log.debug(f"msg ignored:{msg['body']}")
    for_slack.reverse()

    log.debug(f"message for slack:\n{pprint.pformat(for_slack)}")
    return for_slack


def update_with_comments_from_zendesk(event, zendesk_client, slack_client):
    """Handle the raw event from a Zendesk webhook and return without error.

    This will log all exceptions rather than cause zendesk reject 
    our endpoint.

    """
    log = logging.getLogger(__name__)
    
    external_id = event['external_id']
    ticket_id = event['ticket_id']
    if not external_id:
        log.debug(f'external_id is empty, ignoring ticket comment.')    
        return 

    log.debug(f'Recovering ticket by its Zendesk ID:<{ticket_id}>')
    try:
        issue = ZenSlackChat.get_by_ticket(external_id, ticket_id)

    except NotFoundError:
        log.debug(
            f'external_id:<{external_id}> not found, ignoring ticket comment.'
        )    
        return 

    # Recover all messages from the slack conversation:
    slack = []
    resp = slack_client.conversations_replies(
        channel=issue.channel_id, ts=external_id
    )
    for message in resp.data['messages']:
        message['created_at'] = ts_to_datetime(message['ts'])
        slack.append(message)

    # Recover all comments on this ticket:
    zendesk = []
    for comment in zendesk_client.tickets.comments(ticket=ticket_id):
        comment = comment.to_dict()
        comment['created_at'] = utc_to_datetime(comment['created_at'])
        zendesk.append(comment)

    # Work out what needs to be posted to slack:
    for_slack = messages_for_slack(slack, zendesk)

    # Update the slack conversation:
    for message in for_slack:
        msg = f"(Zendesk): {message['body']}"
        post_message(slack_client, external_id, issue.channel_id, msg)
