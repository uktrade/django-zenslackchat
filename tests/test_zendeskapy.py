"""
"""
from unittest.mock import patch
from unittest.mock import MagicMock

from zenslackchat import zendesk_api


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


class FakeApiSearch(object):
    """Aid testing ticket searchs without using Zendesk API directly
    """
    def __init__(self, results=[]):
        self.results = results

    def search(self, chat_id, type):
        return self.results


def test_get_ticket_with_result(log):
    """Verify get_ticket when I expect to get a result.
    """
    chat_id='some-message-id'
    fake_ticket = object()
    search = FakeApiSearch(results=[fake_ticket])

    with patch('zenslackchat.zendesk_api.api', return_value=search):
        returned = zendesk_api.get_ticket(chat_id)

    assert returned == fake_ticket


def test_get_ticket_with_no_result(log):
    """Verify get_ticket when I do not expect to get a result.
    """
    chat_id='some-message-id'
    search = FakeApiSearch()

    with patch('zenslackchat.zendesk_api.api', return_value=search):
        returned = zendesk_api.get_ticket(chat_id)

    assert returned is None
