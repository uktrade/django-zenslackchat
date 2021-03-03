"""
Functions used to aid in zendesk, slack, email messaging.

To simplify testing I keep these functions django free and pass in whats needed 
in arguments. This can then be easily faked/mocked.

Oisin Mulvihill
2020-12-17

"""
import re
import logging
import hashlib
import datetime
from time import mktime
from time import localtime

import emoji
from bs4 import BeautifulSoup
from markdown import markdown
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
    text = text.split('(Zendesk):')[-1].strip()
    text = text.split('(From Zendesk Email):')[-1].strip()
    return text


def strip_formatting(text):
    """Strip all formatting returning only text.    
    """
    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown(text)

    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = ''.join(soup.findAll(text=True))

    # Remove the markdown URLs that may be present after conversion e.g.
    # text like https://QUAY.IO|QUAY.IO leaving QUAY.IO
    text = re.sub(r'(http|https):(\/\/)(.*?)\|', '', text)

    # Regex a modified version of that from https://emailregex.com/
    # replace
    #   MAILER-DAEMON@eu-west-2...com|MAILER-DAEMON@eu-west-2...com
    # with
    #   MAILER-DAEMON@eu-west-2...com
    text = re.sub(
        r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\|)', '', text
    )

    return text


def compare_hash(text):
    return hashlib.sha1(text.encode()).hexdigest()


def strip(text):
    text = text.strip()
    text = strip_zendesk_origin(text)
    text = strip_formatting(text)
    return emoji.emojize(text)


def truncate_email(content, characters=320):
    """Only show a truncated email content.
    
    By default this will return the first 160 characters.

    """
    sample = content[:characters]
    sample_or_full = '...' if len(content) > characters else ''
    email_sample = f"{sample}{sample_or_full}"
    return email_sample


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
        text = strip(msg['text'])
        log.debug(
            f"Text to store for lookup:'{text}' hash:{compare_hash(text)}"
        )
        lookup[compare_hash(text)] = 1        

    # remove api messages which come from slack
    for_slack = []
    for msg in zendesk:
        # Compare like with like, although this might not be needed on zendesk.
        # Apply the zendesk origin filter to prevent repeated email body
        # messages on slack.
        text = strip(strip_signature_from_subject(msg['body']))
        if msg['via']['channel'] == 'email':
            # only show a sample of the email
            text = truncate_email(text)
        msg['body'] = text
        log.debug(f"""


-------------------------------------------------------------------------------

Lookups: {lookup}

Hash:{compare_hash(text)} of Text to compare:'{text}'

Channel: {msg['via']['channel']}

Text present in lookup? {compare_hash(text) in lookup}

-------------------------------------------------------------------------------


""")
        if msg['via']['channel'] == 'api':
            # Exclude the API channel as the bot is posting this message only 
            # for Zendesk e.g. Messages for email user's not needed on slack.
            log.debug(f"Ignoring message from API channel.")

        elif compare_hash(text) not in lookup:
            log.debug(f"msg to be added:'{text}'")
            for_slack.append(msg)

        else:
            log.debug(f"Zendesk message not sent to slack:'{text}'")

    return for_slack
