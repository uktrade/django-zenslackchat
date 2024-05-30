# -*- coding: utf-8 -*-
"""
Functions that handle messages from Zendesk via triggers.

Oisin Mulvihill
2020-12-17

"""

import logging

from webapp import settings
from zenslackchat.message_tools import message_issue_zendesk_url, message_who_is_on_call
from zenslackchat.models import PagerDutyApp, SlackApp, ZendeskApp, ZenSlackChat
from zenslackchat.slack_api import create_thread, message_url
from zenslackchat.zendesk_api import add_comment, get_ticket


def email_from_zendesk(event, slack_client, zendesk_client):
    """Open a ZenSlackChat issue and link it to the existing Zendesk Ticket."""
    log = logging.getLogger(__name__)

    zendesk = ZendeskApp.client()
    slack = SlackApp.client()
    ticket_id = event["ticket_id"]
    channel_id = settings.SRE_SUPPORT_CHANNEL
    user_id = settings.ZENDESK_USER_ID
    group_id = settings.ZENDESK_GROUP_ID
    zendesk_ticket_uri = settings.ZENDESK_TICKET_URI
    slack_workspace_uri = settings.SLACK_WORKSPACE_URI

    # Recover the zendesk issue the email has already created:
    log.debug(f"Recovering ticket from Zendesk:<{ticket_id}>")
    ticket = get_ticket(zendesk, ticket_id)

    # We need to create a new thread for this on the slack channel.
    # We will then add the usual message to this new thread.
    log.debug(f"Success. Got Zendesk ticket<{ticket_id}>")
    # Include descrition as next comment before who is on call to slack
    # to give SREs more context:
    message = f"(From Zendesk Email): {ticket.subject}"
    chat_id = create_thread(slack, channel_id, message)

    # Assign the ticket to ZenSlackChat group and user so comments will
    # come back to us on slack.
    log.debug(f"Assigning Zendesk ticket to User:<{user_id}> and Group:{group_id}")
    # Assign to User/Group
    ticket.assingee_id = user_id
    ticket.group_id = group_id
    # Set to route comments back from zendesk to slack:
    ticket.external_id = chat_id
    zendesk.tickets.update(ticket)

    # Store the zendesk ticket in our db and notify:
    ZenSlackChat.open(channel_id, chat_id, ticket_id=ticket.id)
    message_issue_zendesk_url(
        slack_client, zendesk_ticket_uri, ticket_id, chat_id, channel_id
    )

    app_token = PagerDutyApp.client()

    message_who_is_on_call(
        PagerDutyApp.on_call(app_token=app_token), slack_client, chat_id, channel_id
    )

    # Indicate on the existing Zendesk ticket that the SRE team now knows
    # about this issue.
    slack_chat_url = message_url(slack_workspace_uri, channel_id, chat_id)
    add_comment(
        zendesk_client,
        ticket,
        f"The SRE team is aware of your issue on Slack here {slack_chat_url}.",
    )
