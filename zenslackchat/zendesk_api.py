"""
Wrapper around Zendesk API using the Zenpy library.

To simplify testing I keep these functions django free and pass in whats needed 
in arguments. This can then be easily faked/mocked.

Oisin Mulvihill
2020-08-18

"""
import os
import time
import logging
from urllib.parse import urljoin

from zenpy.lib import exception
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import Comment


def zendesk_ticket_url(zendesk_ticket_uri, ticket_id):
    """Return the link that can be stored in zendesk.

    This handles the trailing slach being present or not. 

    """
    # handle trailing slash being there or not (urljoin doesn't).
    return '/'.join([zendesk_ticket_uri.rstrip('/'), str(ticket_id)])


def get_ticket(client, ticket_id):
    """Recover the ticket by it's ID in zendesk.

    :param client: The Zendesk web client to use.

    :param ticket_id: The Zendesk ID of the Ticket.

    :returns: A Zenpy.TicketAudit instance or None if nothing was found.

    """
    log = logging.getLogger(__name__)
    returned = None

    log.debug(f'Look for Ticket by is Zendesk ID:<{ticket_id}>')
    try:
        returned = client.tickets(id=ticket_id)

    except exception.RecordNotFoundException:
        log.debug(f'Ticket not found by is Zendesk ID:<{ticket_id}>')

    return returned
    

def create_ticket(
    client, chat_id, user_id, group_id, recipient_email, subject, 
    slack_message_url
):
    """Create a new zendesk ticket in response to a new user question.

    :param client: The Zendesk web client to use.

    :param chat_id: The conversation ID on slack.

    :param user_id: Who to create the ticket as.

    :param group_id: Which group the ticket belongs to.

    :param recipient_email: The email addres to CC on the issue.

    :param subject: The title of the support issue.

    :param slack_message_url: The link to message on the support slack channel. 

    :returns: A Zenpy.Ticket instance.

    """    
    log = logging.getLogger(__name__)

    log.debug(
        f'Assigning new ticket subject:<{subject}> to '
        f'user:<{user_id}> and group:<{group_id}> '
    )

    # And assign this ticket to them. I can then later filter comments that 
    # should go to the ZenSlackChat webhook to just those in the ZenSlackChat
    # group.
    issue = Ticket(
        type='ticket', 
        external_id=chat_id,
        requestor_id=user_id,
        submitter_id=user_id,
        assingee_id=user_id,
        group_id=group_id,
        subject=subject, 
        description=subject, 
        recipient=recipient_email,
        comment=Comment(
            body=f'This is the message on slack {slack_message_url}.',
            author_id=user_id
        )        
    )

    log.debug(f'Creating new ticket with subject:<{subject}>')
    ticket_audit = client.tickets.create(issue)

    ticket_id = ticket_audit.ticket.id
    log.debug(f'Ticket for subject:<{subject}> created ok:<{ticket_id}>')

    return ticket_audit.ticket


def add_comment(client, ticket, comment):
    """Add a new comment to an existing ticket.

    :param client: The Zendesk web client to use.

    :param ticket: The Zenpy Ticket instance to use.

    :param comment: The text for the Zendesk comment.

    :returns: The update Zenpy Ticket instance.

    """
    log = logging.getLogger(__name__)

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


def close_ticket(client, ticket_id):
    """Close a ticket in zendesk.

    :param client: The Zendesk web client to use.

    :param ticket_id: The Zendesk Ticket ID.

    :returns: None or Ticket instance closed.

    """
    log = logging.getLogger(__name__)

    log.debug(f'Looking for ticket with ticket_id:<{ticket_id}>')
    ticket = get_ticket(client, ticket_id)
    if ticket.status == 'closed':
        log.warn(f'The ticket:<{ticket.id}> has already been closed!')
    else:
        ticket.status = 'closed'
        client.tickets.update(ticket)
        log.debug(f'Closed ticket:<{ticket.id}> for ticket_id:<{ticket_id}>')

    return ticket
