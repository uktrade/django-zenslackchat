
"""
Functions that handle messages from Zendesk via triggers.

Oisin Mulvihill
2020-12-17

"""
import logging

from webapp import settings
from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat.models import PagerDutyApp
from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError
from zenslackchat.slack_api import message_url
from zenslackchat.slack_api import post_message
from zenslackchat.slack_api import create_thread
from zenslackchat.zendesk_api import get_ticket
from zenslackchat.zendesk_api import add_comment
from zenslackchat.message_tools import ts_to_datetime
from zenslackchat.message_tools import utc_to_datetime
from zenslackchat.message_tools import messages_for_slack
from zenslackchat.message_tools import message_issue_zendesk_url
from zenslackchat.message_tools import message_who_is_on_call


def comments_from_zendesk(event, slack_client, zendesk_client):
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
    resp = slack_client.conversations_replies(
        channel=issue.channel_id, ts=chat_id
    )
    slack = [message for message in resp.data['messages']]
    
    # Recover all comments on this ticket:
    zendesk = [
        comment.to_dict() 
        for comment in zendesk_client.tickets.comments(ticket=ticket_id)
    ]

    # Work out what needs to be posted to slack:
    for_slack = messages_for_slack(slack, zendesk)

    # Update the slack conversation:
    for message in for_slack:
        msg = f"(Zendesk): {message['body']}"
        post_message(slack_client, chat_id, issue.channel_id, msg)

    return for_slack