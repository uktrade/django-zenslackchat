"""
Wrapper around Zendesk API using the Zenpy library.

Oisin Mulvihill
2020-08-18

"""
import os
import time
import logging
from urllib.parse import urljoin

from zenpy import Zenpy
from zenpy.lib import exception
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import Comment


def config():
    """Recover the configuration for Zenpy from the environment."""
    return dict(
        email=os.environ.get('ZENDESK_EMAIL', '<email@example.com>'),
        token=os.environ.get('ZENDESK_TOKEN', '<token>'),
        subdomain=os.environ.get('ZENDESK_SUBDOMAIN', '<something>'),
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


def get_ticket(ticket_id):
    """Recover the ticket by it's ID in zendesk.

    :param ticket_id: The Zendesk ID of the Ticket.

    :returns: A Zenpy.Ticket instance or None if nothing was found.

    """
    log = logging.getLogger(__name__)
    returned = None

    client = api()

    log.debug(f'Look for Ticket by is Zendesk ID:<{ticket_id}>')
    try:
        returned = client.tickets(id=ticket_id)

    except exception.RecordNotFoundException:
        log.debug(f'Ticket not found by is Zendesk ID:<{ticket_id}>')

    return returned


def create_ticket(external_id, recipient_email, subject, slack_message_url):
    """Create a new zendesk ticket in response to a new user question.
    """    
    log = logging.getLogger(__name__)

    client = api()

    requestor = client.users.me()
    log.debug(f'Recovered my requestor id:<{requestor.id}>')

    issue = Ticket(
        type='question', 
        external_id=external_id,
        subject=subject, 
        description=subject, 
        recipient=recipient_email,
        requestor_id=requestor.id,
        comment=Comment(
            body=f'This is the message on slack {slack_message_url}.',
            author_id=requestor.id
        )        
    )

    log.debug(f'Creating new ticket with subject:<{subject}>')
    ticket_audit = client.tickets.create(issue)

    ticket_id = ticket_audit.ticket.id
    log.debug(f'Ticket for subject:<{subject}> created ok:<{ticket_id}>')

    return ticket_audit.ticket


def add_comment(ticket, comment):
    """Add a new comment to an existing ticket.

    :param ticket: The Zenpy Ticket instance to use.

    :param comment: The text for the Zendesk comment.

    :returns: The update Zenpy Ticket instance.

    """
    log = logging.getLogger(__name__)
    client = api()

    requestor = client.users.me()
    log.debug(f'Recovered my requestor id:<{requestor.id}>')

    log.debug(f'Adding comment to ticket:<{ticket.id}>')
    ticket.comment = Comment(
        body=comment,
        author_id=requestor.id
    )
    client.tickets.update(ticket)
    log.debug(f'Added comment:<{comment}> to ticket:<{ticket.id}>')

    return ticket


def close_ticket(external_id):
    """Close a ticket in zendesk.

    :param external_id: The message id stored as the external_id in zendesk.

    :returns: None or Ticket instance closed.

    """
    log = logging.getLogger(__name__)
    client = api()

    log.debug(f'Looking for ticket with external_id:<{external_id}>')
    ticket = get_ticket(external_id)
    if ticket:
        ticket.status = 'closed'
        client.tickets.update(ticket)
        log.debug(f'Closed ticket:<{ticket.id}> for external_id:<{external_id}>')

    return ticket
