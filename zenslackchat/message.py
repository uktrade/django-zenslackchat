# -*- coding: utf-8 -*-
"""
The main bot message handler.

This determines how to react to messages we receive from slack.

Oisin Mulvihill
2020-08-20

"""

import logging

import zenpy

from webapp import settings
from zenslackchat.message_tools import (
    is_resolved,
    message_issue_zendesk_url,
    message_who_is_on_call,
    ts_to_datetime,
)
from zenslackchat.models import (
    NotFoundError,
    OutOfHoursInformation,
    PagerDutyApp,
    ZenSlackChat,
)
from zenslackchat.slack_api import message_url, post_message
from zenslackchat.zendesk_api import (
    add_comment,
    close_ticket,
    create_ticket,
    get_ticket,
    zendesk_ticket_url,
)

# See https://api.slack.com/events/message for subtypes. (we allow bot_message)
IGNORED_SUBTYPES = [
    "channel_archive",
    "channel_join",
    "channel_leave",
    "channel_name",
    "channel_purpose",
    "channel_topic",
    "channel_unarchive",
    "ekm_access_denied",
    "file_comment",
    "file_mention",
    "group_archive",
    "group_join",
    "group_leave",
    "group_name",
    "group_purpose",
    "group_topic",
    "group_unarchive",
    "me_message",
    "message_changed",
    "message_deleted",
    "message_replied",
    "pinned_item",
    "thread_broadcast",
    "unpinned_item",
    "channel_rename",
]

# "file_share" was ignored. I don't handle the files attached, however I
# respond to the message now. Users were posting screenshots with issue
# description and the bot was ignoring this.


def handler(
    event,
    our_channel,
    workspace_uri,
    zendesk_uri,
    slack_client,
    zendesk_client,
    user_id,
    group_id,
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

    text = event.get("text", "")

    bot_id = event.get("bot_id")
    if bot_id and bot_id not in settings.ALLOWED_BOT_IDS:
        log.debug(f"Ignoring bot ({bot_id}) message to prevent repeats: {text}")
        return False

    channel_id = event.get("channel", "").strip()
    if channel_id != our_channel:
        if settings.DEBUG:
            log.debug(
                f"Ignoring event from channel id:<{channel_id} as its not from"
                f"our support channel id:{our_channel}"
            )
        return False

    subtype = event.get("subtype")
    if subtype in IGNORED_SUBTYPES:
        log.debug(f"Ignoring subtype we don't handle: {subtype}")
        return False

    if settings.DISABLE_MESSAGE_PROCESSING:
        log.warn(
            "MESSAGE HANDLING IS DISABLED! "
            f"Not handled from channel<{channel_id}>: {text}"
        )
        return False

    log.debug(f"New message on support channel<{channel_id}>: {text}")

    chat_id = event["ts"]
    # Only present in a new top-level message
    thread_id = event.get("thread_ts", "")

    real_name = None
    recipient_email = None

    if subtype == "bot_message":
        real_name = event.get("username", "Unnamed bot")
        recipient_email = None
    else:
        slack_user_id = event["user"]

        # Recover the slack channel message author's email address. I assume
        # this is always set on all accounts.
        log.debug(f"Recovering profile for user <{slack_user_id}>")
        resp = slack_client.users_info(user=slack_user_id)
        # print(f"resp.event:\n{resp.event}\n")
        real_name = resp.data["user"]["real_name"]
        recipient_profile = resp.data["user"].get("profile")
        if not recipient_profile and not bot_id:
            log.error(
                f"For slack user '{real_name}' I was not able to recover a profile."
            )
            return False

        recipient_email = None
        if recipient_profile:
            recipient_email = recipient_profile.get("email", "")
            if not recipient_email and not bot_id:
                log.error(
                    f"For slack profile '{real_name}' I was not able to recover an "
                    "email. Is the bot token scope users:read.email set? (Re)install "
                    "the slack app?"
                )
                return False

    # zendesk ticket instance
    ticket = None

    # Get any existing ticket from zendesk:
    if chat_id and thread_id:
        log.debug(f"Received thread message from '{recipient_email}': {text}\n")

        # This is a reply message, use the thread_id to recover the parent
        # message:
        slack_chat_url = message_url(workspace_uri, channel_id, thread_id)
        try:
            issue = ZenSlackChat.get(channel_id, thread_id)

        except NotFoundError:
            # This could be an thread that happened before the bot was running:
            log.warning(f"No ticket found in slack {slack_chat_url}. Old thread?")

        else:
            # If this is a command handle it otherwise ship it as a comment to
            # Zendesk. You can only add comments if the Zendesk ticket is not
            # closed.
            ticket_id = issue.ticket_id
            url = zendesk_ticket_url(zendesk_uri, ticket_id)
            ticket = get_ticket(zendesk_client, ticket_id)
            log.debug(f"Recoverd ticket {ticket_id} from slack {slack_chat_url}")
            command = text.strip().lower()
            if is_resolved(command):
                # Time to close the ticket as the issue has been resolved.
                log.debug(f"Closing ticket {ticket_id} from slack {slack_chat_url}.")
                close_ticket(zendesk_client, ticket_id)
                ZenSlackChat.resolve(channel_id, thread_id)
                post_message(
                    slack_client,
                    thread_id,
                    channel_id,
                    f"🤖 Understood. Ticket {url} has been closed.",
                )

            elif command == "help":
                post_message(
                    slack_client,
                    thread_id,
                    channel_id,
                    "I understand the follow commands:\n\n"
                    "- help: <this command>\n"
                    "- resolve, resolve ticket, ✅, 🆗: close this ticket "
                    f"({url})\n"
                    "\nBest regards.\n\n🤖",
                )

            else:
                if ticket.status == "closed":
                    post_message(
                        slack_client,
                        thread_id,
                        channel_id,
                        f"🤖 This ticket is closed {url}. Please raise a "
                        "new support issue.",
                    )

                else:
                    # Send this message on to Zendesk.
                    add_comment(zendesk_client, ticket, f"{real_name} (Slack): {text}")

    else:
        slack_chat_url = message_url(workspace_uri, channel_id, chat_id)
        try:
            issue = ZenSlackChat.get(channel_id, chat_id)
        except NotFoundError:
            # No issue found. It looks like its new issue:
            log.debug(f"Received message from '{recipient_email}': {text}\n")
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
                    slack_client,
                    thread_id,
                    channel_id,
                    "🤖 I'm unable to talk to Zendesk (API Error).",
                )
                log.exception("Zendesk API error: ")

            else:
                # Store all the details and notify:
                log.debug("open ticket")
                ZenSlackChat.open(channel_id, chat_id, ticket_id=ticket.id)
                message_issue_zendesk_url(
                    slack_client, zendesk_uri, ticket.id, chat_id, channel_id
                )
                log.debug("get PD login")
                app_token = PagerDutyApp.client()

                #  :returns: dict(primary='First Lastname', secondary='First Lastname')
                log.debug("Rota section")
                log.debug(f"{slack_client}, {chat_id}, {channel_id}")
                if settings.USE_ATLASSIAN:
                    log.debug("Getting rota from Confluence.")
                    message_who_is_on_call(
                        {"primary": "Peter Parker", "secondary": "Bruce Banister"},
                        slack_client,
                        chat_id,
                        channel_id,
                    )
                else:
                    log.debug("Getting rota from PD.")
                    message_who_is_on_call(
                        PagerDutyApp.on_call(app_token=app_token),
                        slack_client,
                        chat_id,
                        channel_id,
                    )

                # Is this an issue created out of hours?
                OutOfHoursInformation.inform_if_out_of_hours(
                    # ID is UTC epoch time. I use this for the 'now' time. This
                    # should handle any delay with messages from slack to the
                    # bot.
                    ts_to_datetime(chat_id),
                    chat_id,
                    channel_id,
                    slack_client,
                )

        else:
            # No, we have a ticket already for this.
            log.info(f"The issue '{text}' is already in Zendesk '{chat_id}'")

    return True
