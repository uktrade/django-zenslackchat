"""
Wrapper around Zendesk API using the Zenpy library.

Oisin Mulvihill
2020-08-18

"""
import os
from urllib.parse import urljoin

from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import Comment


def config():
    """Recover the configuration for Zenpy from the environment."""
    return dict(
        email=os.environ.get('ZENDESK_EMAIL', '<email@example.com>'),
        token=os.environ.get('ZENDESK_TOKEN', '<token>'),
        subdomain=os.environ.get('ZENDESK_SUBDOMAIN', '<something>'),
        slack_url_field=os.environ.get(
            'ZENDESK_SLACK_URL_FIELD', 
            '360013308180'
        ),
    )


def api():
    """Returns a configured Zenpy client instance ready for use.

    This expects the environment to be set:

        - ZENDESK_EMAIL
        - ZENDESK_TOKEN
        - ZENDESK_SUBDOMAIN

    This currently uses the Token based Zendesk API key. We need to move to
    OAuth based system for more granular access to just what is needed.

    """
    cfg = config()

    return Zenpy(
        email=cfg['email'],
        subdomain=cfg['subdomain'],
        token=cfg['token']
    )


def zendesk_ticket_url(ticket_id):
    """Return the link that can be stored in zendesk.

    This expects the environment variable ZENDESK_TICKET_URI to be set. 

    """
    ZENDESK_TICKET_URI = os.environ.get(
        'ZENDESK_TICKET_URI', 
        'https://zendesk.example.com/agent/tickets/'
    )

    # handle trailing slash being there or not (urljoin doesn't).
    return '/'.join([ZENDESK_TICKET_URI.rstrip('/'), str(ticket_id)])


def get_ticket(chat_id):
    """Recover the zendesk ticket for a given slack parent message.

    :param chat_id: The 'ts' payload used by slack to identify a message.

    :returns: A Zenpy.Ticket instance or None if nothing was found.

    """
    returned = None

    client = api()

    # Return the first item found, in theory there should only be one.
    #
    # I can't seem to get tickets by external_id directly. I need to do a 
    # search like this :(
    results = [item for item in client.search(chat_id, type='ticket')]
    if len(results) > 0:
        returned = results[0]

    return returned


def create_ticket(chat_id, recipient_email, subject, slack_message_url):
    """Create a new zendesk ticket in response to a new user question.
    """    
    slack_url_field = config()['slack_url_field']

    client = api()

    requestor = client.users.me()

    issue = Ticket(
        type='question', 
        external_id=chat_id,
        subject=subject, 
        description=subject, 
        recipient=recipient_email,
        requestor_id=requestor.id,
        custom_fields=[dict(
            id=slack_url_field,
            value=slack_message_url
        )],
        comment=Comment(
            body=f'This is the message on slack {slack_message_url}.',
            author_id=requestor.id
        )        
    )

    ticket_audit = client.tickets.create(issue)

    return ticket_audit.ticket


def close_ticket(chat_id):
    """
    """
    client = api()

    ticket = get_ticket(chat_id)
    if ticket:
        ticket.status = 'closed'
        client.tickets.update(ticket)

    return ticket
