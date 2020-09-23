"""
"""
from unittest.mock import patch
from unittest.mock import MagicMock

from zenslackchat import zendesk_api


class FakeUserResponse(object):
    def __init__(self, user_id):
        self.id = user_id


class FakeTicket(object):
    def __init__(self, ticket_id):
        self.id = ticket_id
        self.status = 'open'


class FakeTicketAudit(object):
    def __init__(self, ticket):
        self.ticket = ticket


class FakeApi(object):
    """Aid testing tickets without using Zendesk API directly.
    """
    class FakeUsers(object):
        def __init__(self, me=None):
            self._me = me

        def me(self):
            return self._me

    class FakeTicketCRUD(object):        
        def __init__(self, parent, ticket_audit=None):
            self.ticket_audit = ticket_audit
            self.parent = parent

        def update(self, ticket):
            """No actual update performed
            """

        def create(self, ticket):
            """Pretend to create a zendesk ticket and return the canned
            result.
            """
            self.parent.created_tickets.append(ticket)
            return self.ticket_audit

        def __call__(self, id):
            """Recover a specific ticket.
            """
            returned = None

            if self.ticket_audit:
                returned = self.ticket_audit.ticket

            return returned

    def __init__(self, results=[], me=None, ticket_audit=None):
        self.results = results
        self.users = self.FakeUsers(me)
        self.created_tickets = []
        self.tickets = self.FakeTicketCRUD(self, ticket_audit)

    def search(self, chat_id, type):
        return self.results



def test_zendesk_ticket_url(log):
    """Verify the URL generated to point at (UI not API) ticket in zendesk.
    """
    # check trailing and non-trailing slash set
    zendesk_ticket_url = 'https://example.com/agent/tickets'
    url = zendesk_api.zendesk_ticket_url(zendesk_ticket_url, '123')
    assert url == 'https://example.com/agent/tickets/123'

    zendesk_ticket_url = 'https://help.example.com/agent/tickets/'
    url = zendesk_api.zendesk_ticket_url(zendesk_ticket_url, '123')
    assert url == 'https://help.example.com/agent/tickets/123'

    # handle integer ticket ID being passed in e.g. ticket.id
    zendesk_ticket_url = 'https://frog.example.com/agent/tickets/'
    url = zendesk_api.zendesk_ticket_url(zendesk_ticket_url, 17)
    assert url == 'https://frog.example.com/agent/tickets/17'


def test_get_ticket_with_result(log):
    """Verify get_ticket when I expect to get a result.
    """
    fake_ticket = FakeTicket(ticket_id=12345)
    fake_ticket_audit = FakeTicketAudit(fake_ticket)
    client = FakeApi(results=[fake_ticket], ticket_audit=fake_ticket_audit)

    returned = zendesk_api.get_ticket(client, 12345)

    assert returned == fake_ticket


def test_get_ticket_with_no_result(log):
    """Verify get_ticket when I do not expect to get a result.
    """
    chat_id='some-message-id'
    client = FakeApi()

    returned = zendesk_api.get_ticket(client, chat_id)

    assert returned is None


def test_create_ticket(log):
    """Test out the behaviour when 'creating' a zendesk ticket.
    """
    user_id= '100000000001'
    group_id= '200000000002'
    recipient_email = 'bob@example.com'
    subject = 'printer out of ink'
    slack_message_url = 'https://example.com/channel/chat_id'
    fake_ticket = FakeTicket(ticket_id='some-ticket-id')
    fake_ticket_audit = FakeTicketAudit(fake_ticket)
    client = fake_api = FakeApi(
        results=[fake_ticket],
        me=FakeUserResponse(user_id),
        ticket_audit=fake_ticket_audit
    )

    zendesk_api.create_ticket(
        client,
        user_id,
        group_id,
        recipient_email,
        subject,
        slack_message_url
    )

    assert len(fake_api.created_tickets) == 1
    ticket = fake_api.created_tickets[0]
    assert ticket.type == 'ticket'
    assert ticket.subject == subject
    assert ticket.recipient == recipient_email
    assert ticket.submitter_id == user_id
    assert ticket.assingee_id == user_id
    assert ticket.group_id == group_id
    assert ticket.comment.author_id == user_id
    msg = f'This is the message on slack {slack_message_url}.'
    assert ticket.comment.body == msg


def test_close_ticket(log):
    """Verify get_ticket when I expect to get a result.
    """
    fake_ticket = FakeTicket(ticket_id=12345)
    fake_ticket_audit = FakeTicketAudit(fake_ticket)
    assert fake_ticket.status == 'open'
    client = FakeApi(results=[fake_ticket], ticket_audit=fake_ticket_audit)

    returned = zendesk_api.close_ticket(client, 12345)

    assert returned == fake_ticket
    assert fake_ticket.status == 'closed'
