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

    def __init__(self, results=[], me=None, ticket_audit=None):
        self.results = results
        self.users = self.FakeUsers(me)
        self.created_tickets = []
        self.tickets = self.FakeTicketCRUD(self, ticket_audit)

    def search(self, chat_id, type):
        return self.results


def test_zapi_client_default_config(log):
    """Verify the default Zenpy config env variables.
    """
    # make sure no ZENDESK_* variables are set to interfere with test.
    with patch.dict('os.environ', {}, clear=True):    
        config = zendesk_api.config()    

    assert config['email'] == '<email@example.com>'
    assert config['token'] == '<token>'
    assert config['subdomain'] == '<something>'


def test_zapi_client_from_env_config(log):
    """Verify the default Zenpy config env variables.
    """
    mock_env = {
        'ZENDESK_EMAIL': 'tony@example.com',
        'ZENDESK_TOKEN': 'token1234',
        'ZENDESK_SUBDOMAIN': 'helpsubdomain.example.com' 
    }

    with patch.dict('os.environ', mock_env, clear=True):    
        config = zendesk_api.config()    

    assert config['email'] == 'tony@example.com'
    assert config['token'] == 'token1234'
    assert config['subdomain'] == 'helpsubdomain.example.com'


def test_zendesk_ticket_url(log):
    """Verify the URL generated to point at (UI not API) ticket in zendesk.
    """
    # default: nothing set in env
    with patch.dict('os.environ', {}, clear=True):    
        url = zendesk_api.zendesk_ticket_url('123')
    assert url == 'https://zendesk.example.com/agent/tickets/123'

    # check trailing and non-trailing slash set
    env = {'ZENDESK_TICKET_URI': 'https://example.com/agent/tickets/'}
    with patch.dict('os.environ', env, clear=True):    
        url = zendesk_api.zendesk_ticket_url('123')
    assert url == 'https://example.com/agent/tickets/123'

    env = {'ZENDESK_TICKET_URI': 'https://help.example.com/agent/tickets'}
    with patch.dict('os.environ', env, clear=True):    
        url = zendesk_api.zendesk_ticket_url('17')
    assert url == 'https://help.example.com/agent/tickets/17'

    # handle integer ticket ID being passed in e.g. ticket.id
    env = {'ZENDESK_TICKET_URI': 'https://help.example.com/agent/tickets'}
    with patch.dict('os.environ', env, clear=True):    
        url = zendesk_api.zendesk_ticket_url(17)
    assert url == 'https://help.example.com/agent/tickets/17'


def test_get_ticket_with_result(log):
    """Verify get_ticket when I expect to get a result.
    """
    chat_id='some-message-id'
    fake_ticket = FakeTicket(ticket_id=chat_id)
    fake_api = FakeApi(results=[fake_ticket])

    with patch('zenslackchat.zendesk_api.api', return_value=fake_api):
        returned = zendesk_api.get_ticket(chat_id)

    assert returned == fake_ticket


def test_get_ticket_with_no_result(log):
    """Verify get_ticket when I do not expect to get a result.
    """
    chat_id='some-message-id'
    fake_api = FakeApi()

    with patch('zenslackchat.zendesk_api.api', return_value=fake_api):
        returned = zendesk_api.get_ticket(chat_id)

    assert returned is None


def test_create_ticket(log):
    """
    """
    user_id= 'some-user-id'
    chat_id = 'some-message-id'
    recipient_email = 'bob@example.com'
    subject = 'printer out of ink'
    slack_message_url = 'https://example.com/channel/chat_id'
    fake_ticket = FakeTicket(ticket_id=chat_id)
    fake_ticket_audit = FakeTicketAudit(fake_ticket)
    fake_api = FakeApi(
        results=[fake_ticket],
        me=FakeUserResponse(user_id),
        ticket_audit=fake_ticket_audit
    )
    assert fake_ticket.status == 'open'

    with patch('zenslackchat.zendesk_api.api', return_value=fake_api):
        zendesk_api.create_ticket(
            chat_id,
            recipient_email,
            subject,
            slack_message_url
        )

    assert len(fake_api.created_tickets) == 1
    ticket = fake_api.created_tickets[0]
    assert ticket.type == 'question'
    assert ticket.external_id == chat_id
    assert ticket.subject == subject
    assert ticket.recipient == recipient_email
    assert ticket.requestor_id == user_id
    assert ticket.comment.author_id == user_id
    msg = f'This is the message on slack {slack_message_url}.'
    assert ticket.comment.body == msg


def test_close_ticket(log):
    """Verify get_ticket when I expect to get a result.
    """
    chat_id='some-message-id'
    fake_ticket = FakeTicket(ticket_id=chat_id)
    fake_api = FakeApi(results=[fake_ticket])
    assert fake_ticket.status == 'open'

    with patch('zenslackchat.zendesk_api.api', return_value=fake_api):
        returned = zendesk_api.close_ticket(chat_id)

    assert returned == fake_ticket
    assert fake_ticket.status == 'closed'
