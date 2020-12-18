"""
Functions used to aid in zendesk, slack, email messaging.

To simplify testing I keep these functions django free and pass in whats needed 
in arguments. This can then be easily faked/mocked.

Oisin Mulvihill
2020-12-17

"""
import datetime
import logging
from time import mktime
from time import localtime

import emoji
from dateutil.parser import parse

from zenslackchat.slack_api import post_message
from zenslackchat.zendesk_api import zendesk_ticket_url


def message_who_is_on_call(on_call, slack_client, chat_id, channel_id):
    """Post to the chat who is primary and secondary on call.

    This will only message if the PagerDutyApp / OAuth set up has been done.
    
    """
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


def ts_to_datetime(epoch):
    """Convert raw UTC slack message epoch times to datetime.

    :param epoch: A string epoch decimal e.g. '1598459584.013100' 

    :returns: datetime.datetime(2020, 8, 26, 17, 33, 4, tzinfo=utc)

    """
    dt = datetime.datetime.fromtimestamp(mktime(localtime(float(epoch))))
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


def strip_signature_from_subject(content):
    """Assume --\n is marker for email signature and return everything before.
    """
    return content.split('--')[0]


def strip_zendesk_origin(text):
    return text.split('(Zendesk):')[-1].strip()


def messages_for_slack(slack, zendesk):
    """Work out which messages from zendesk need to be added to the slack 
    conversation.

    :param slack: A list of slack messages.

    :param zendesk: A list of zendesk comment message.

    :returns: An empty list or list of messages to be added.

    """
    log = logging.getLogger(__name__)

    lookup = {}
    for msg in slack:
        # text = msg['text']
        # convert '... :palm_tree:​ ...' to its emoji character 🌴
        # Slack seems to use the name whereas zendesk uses the actual emoji:
        text = emoji.emojize(strip_zendesk_origin(msg['text']))
        log.debug(f"Text to store for lookup: {text}")
        lookup[text] = 1        

    # remove api messages which come from slack
    for_slack = []
    for msg in zendesk:
        # Compare like with like, although this might not be needed on zendesk.
        # Apply the zendesk origin filter to prevent repeated email body
        # messages on slack.
        text = strip_signature_from_subject(msg['body'])
        text = strip_zendesk_origin(text)
        text = emoji.emojize(text)
        log.debug(f"Text to compare to compare with lookup: {text}")
        log.debug(f"Texts in lookup: {lookup}")

        # allow email/web/other channels excluding api which bot sends on.
        if msg['via']['channel'] != 'api' and text not in lookup:
            log.debug(f"msg to be added: {text}")
            if msg['via']['channel'] == 'email':
                msg['body'] = strip_signature_from_subject(msg['body'])            
            for_slack.append(msg)
        else:
            log.debug(f"Zendesk message not sent to slack: {text}")

    return for_slack
