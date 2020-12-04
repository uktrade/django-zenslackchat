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

import emoji
import zenpy
from dateutil.parser import parse

from webapp import settings
from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat.models import PagerDutyApp
from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError
from zenslackchat.slack_api import message_url
from zenslackchat.slack_api import create_thread
from zenslackchat.slack_api import post_message
from zenslackchat.zendesk_api import get_ticket
from zenslackchat.zendesk_api import add_comment
from zenslackchat.zendesk_api import close_ticket
from zenslackchat.zendesk_api import create_ticket
from zenslackchat.zendesk_api import zendesk_ticket_url


# See https://api.slack.com/events/message for subtypes.
IGNORED_SUBTYPES = [
    "bot_message", "channel_archive", "channel_join", "channel_leave", 
    "channel_name", "channel_purpose", "channel_topic", "channel_unarchive", 
    "ekm_access_denied", "file_comment", "file_mention", "file_share", 
    "group_archive", "group_join", "group_leave", "group_name", 
    "group_purpose", "group_topic", "group_unarchive", "me_message", 
    "message_changed", "message_deleted", "message_replied", "pinned_item", 
    "thread_broadcast", "unpinned_item", "channel_rename"
]


def message_who_is_on_call(slack_client, chat_id, channel_id):
    """Post to the chat who is primary and secondary on call.

    This will only message if the PagerDutyApp / OAuth set up has been done.
    
    """
    on_call = PagerDutyApp.on_call()
    if on_call != {}:
        message = (
            f"📧 Primary on call: {on_call['primary']}\n"
            f"ℹ️ Secondary on call: {on_call['secondary']}."
        )
        post_message(slack_client, chat_id, channel_id, message)


def message_issue_zendesk_url(
    slack_client, zendesk_uri, ticket_id, chat_id, channel_id
):
    """Post to slack where the Zendesk URL of the issue.
    """
    url = zendesk_ticket_url(zendesk_uri, ticket_id)
    message = f"Hello, your new support request is {url}"
    post_message(slack_client, chat_id, channel_id, message)


def is_resolved(command):
    """Return true if the given command string matches on of the accepted
    resolve strings.

    :param command: A string of 'resolve', 'resolve ticket', '🆗' or '✅'

    :returns: True the given string is a resolve command otherwise False.

    """
    _cmd = emoji.emojize(command.lower(), use_aliases=True)
    return (
        _cmd == 'resolve' or 
        _cmd == 'resolve ticket' or 
        _cmd == '🆗' or
        _cmd == '✅'
    )


def handler(
    event, our_channel, workspace_uri, zendesk_uri, slack_client, 
    zendesk_client, user_id, group_id
):
    """Decided what to do with the message we have received.

    :param event: The slack event received.

    :param our_channel: The slack channel id we listen to.

    All other events on different channels are silently ignored.

    :param workspace_uri: The base link to slack workspace archives.

    :param zendesk_uri: The base link to zendesk agent tickets.

    :param slack_client: The slack web client instance.

    :param zendesk_client: The Zendesk web client instance.

    :param user_id: Who to create Zendesk tickets as.

    :param group_id: Which Zendesk group the ticket belongs to.

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
    
    # I'm ignoring most subtypes, I might be able to ignore all. I can manage 
    # the message / message-reply based on the ts/thread_ts fields and whether 
    # they are populated or not. I'm calling 'ts' chat_id and 'thread_ts' 
    # thread_id.
    subtype = event.get('subtype')
    if subtype in IGNORED_SUBTYPES:
        log.debug(f"Ignoring subtype we don't handle: {subtype}")
        return False

    if settings.DISABLE_MESSAGE_PROCESSING:
        log.warn(
            "MESSAGE HANDLING IS DISABLED! "
            f"Not handled from channel<{channel_id}>: {text}"
        )
        return False

    else:
        log.debug(f"New message on support channel<{channel_id}>: {text}")

    # A message
    slack_user_id = event['user']
    chat_id = event['ts']
    # won't be present in a new top-level message we will reply too
    thread_id = event.get('thread_ts', '')

    # Recover the slack channel message author's email address. I assume 
    # this is always set on all accounts.
    log.debug(f"Recovering profile for user <{slack_user_id}>")
    resp = slack_client.users_info(user=slack_user_id)
    # print(f"resp.event:\n{resp.event}\n")
    real_name = resp.data['user']['real_name']
    recipient_email = resp.data['user']['profile'].get('email', '')
    if not recipient_email:
        log.error(
            f"For slack profile '{real_name}' I was not able to recover an "
            "email. Is the bot token scope users:read.email set? (Re)install "
            "the slack app?"
        )
        # hmm this is not the answer as its getting into a loop :(
        return False

    # zendesk ticket instance
    ticket = None

    # Get any existing ticket from zendesk:
    if chat_id and thread_id:
        log.debug(
            f"Received thread message from '{recipient_email}': {text}\n"
        )

        # This is a reply message, use the thread_id to recover the parent 
        # message:
        slack_chat_url = message_url(workspace_uri, channel_id, thread_id)
        try:
            issue = ZenSlackChat.get(channel_id, thread_id)

        except NotFoundError:
            # This could be an thread that happened before the bot was running:
            log.warning(
                f'No ticket found in slack {slack_chat_url}. Old thread?'
            )

        else:
            # If this is a command handle it otherwise ship it as a comment to
            # Zendesk. You can only add comments if the Zendesk ticket is not
            # closed.
            ticket_id = issue.ticket_id
            url = zendesk_ticket_url(zendesk_uri, ticket_id)
            ticket = get_ticket(zendesk_client, ticket_id)
            log.debug(
                f'Recoverd ticket {ticket_id} from slack {slack_chat_url}'
            )
            command = text.strip().lower()
            if is_resolved(command):
                # Time to close the ticket as the issue has been resolved.
                log.debug(
                    f'Closing ticket {ticket_id} from slack {slack_chat_url}.'
                )
                close_ticket(zendesk_client, ticket_id)
                ZenSlackChat.resolve(channel_id, thread_id)
                post_message(
                    slack_client, thread_id, channel_id, 
                    f'🤖 Understood. Ticket {url} has been closed.'
                )

            elif command == 'help':
                post_message(
                    slack_client, thread_id, channel_id, (
                       "I understand the follow commands:\n\n" 
                       "- help: <this command>\n"
                       "- resolve, resolve ticket, ✅, 🆗: close this ticket "
                       f"({url})\n"
                       "\nBest regards.\n\n🤖"
                    )
               )

            else:
                if ticket.status == 'closed':
                    post_message(
                        slack_client, thread_id, channel_id, 
                        f"🤖 This ticket is closed {url}. Please raise a "
                        "new support issue."
                    )

                else:
                    # Send this message on to Zendesk.
                    add_comment(
                        zendesk_client, 
                        ticket, 
                        f"{real_name} (Slack): {text}"
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
                    chat_id=chat_id,
                    user_id=user_id, 
                    group_id=group_id,
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
                # Store all the details and notify:
                ZenSlackChat.open(channel_id, chat_id, ticket_id=ticket.id)
                message_issue_zendesk_url(
                    slack_client, zendesk_uri, ticket.id, chat_id, channel_id                    
                )
                message_who_is_on_call(slack_client, chat_id, channel_id)

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
    # msgs = [s['text'] for s in slack]
    # log.debug(f"Raw Slack messages:\n{slack}")
    # log.debug(f"Slack messages:\n{msgs}")

    zendesk = sorted(zendesk, key=itemgetter('created_at'), reverse=True) 
    # msgs = [z['body'] for z in zendesk]
    # log.debug(f"Zendesk messages:\n{msgs}")

    # Ignore the first message which is the parent message. Also ignore the 
    # second message which is our "link to zendesk ticket" message.
    lookup = {}
    for msg in slack[2:]:
        # text = msg['text']
        # convert '... :palm_tree:​ ...' to its emoji character 🌴
        # Slack seems to use the name whereas zendesk uses the actual emoji:
        raw_text = msg['text'].split('(Zendesk):')[-1].strip()
        text = emoji.emojize(raw_text)
        # log.debug(f"slack msg to index:{text}")
        lookup[text] = 1        
    # log.debug(f"messages to consider from slack:{len(slack)}")
    # log.debug(f"lookup:\n{lookup}")

    # remove api messages which come from slack
    for_slack = []
    for msg in zendesk:
        # compare like with like, although this might not be needed on zendesk
        text = emoji.emojize(msg['body'])
        if msg['via']['channel'] == 'web' and text not in lookup:
            # log.debug(f"msg to be added:{text}")
            for_slack.append(msg)
        # else:
        #     log.debug(f"msg ignored:{text}")
    for_slack.reverse()

    # log.debug(f"message for slack:\n{pprint.pformat(for_slack)}")
    return for_slack


def update_with_comments_from_zendesk(event, slack_client, zendesk_client):
    """Handle the raw event from a Zendesk webhook and return without error.

    This will log all exceptions rather than cause zendesk reject 
    our endpoint.

    """
    log = logging.getLogger(__name__)
    
    chat_id = event['chat_id']
    ticket_id = event['ticket_id']
    if not chat_id:
        log.debug(f'chat_id is empty, ignoring ticket comment.')    
        return 

    log.debug(f'Recovering ticket by its Zendesk ID:<{ticket_id}>')
    try:
        issue = ZenSlackChat.get_by_ticket(chat_id, ticket_id)

    except NotFoundError:
        log.debug(
            f'chat_id:<{chat_id}> not found, ignoring ticket comment.'
        )    
        return 

    # Recover all messages from the slack conversation:
    slack = []
    resp = slack_client.conversations_replies(
        channel=issue.channel_id, ts=chat_id
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
        post_message(slack_client, chat_id, issue.channel_id, msg)


def update_from_zendesk_email(event, slack_client, zendesk_client):
    """Open a ZenSlackChat issue and link it to the existing Zendesk Ticket.

    """
    log = logging.getLogger(__name__)

    zendesk = ZendeskApp.client()
    slack = SlackApp.client()    
    channel_id = event['channel_id']
    ticket_id = event['ticket_id']
    zendesk_uri = event['zendesk_uri']
    workspace_uri = event['workspace_uri']

    # Recover the zendesk issue the email has already created:
    log.debug(f'Recovering ticket from Zendesk:<{ticket_id}>')
    ticket = get_ticket(zendesk, ticket_id)

    # We need to create a new thread for this on the slack channel.
    # We will then add the usual message to this new thread.
    log.debug(f'Success. Got Zendesk ticket<{ticket_id}>')
    message = f"(From Zendesk Email): {ticket.description}"
    chat_id = create_thread(slack, channel_id, message)

    # Store the zendesk ticket in our db and notify:
    ZenSlackChat.open(channel_id, chat_id, ticket_id=ticket.id)
    message_issue_zendesk_url(
        slack_client, zendesk_uri, ticket_id, chat_id, channel_id                    
    )
    message_who_is_on_call(slack_client, chat_id, channel_id)

    # Indicate on the existing Zendesk ticket that the SRE team now knows
    # about this issue.
    slack_chat_url = message_url(workspace_uri, channel_id, chat_id)
    add_comment(
        zendesk_client, 
        ticket, 
        f'The SRE team is aware of your issue on Slack here {slack_chat_url}.'
    )

