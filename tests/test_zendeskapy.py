"""
"""
import pytest

from zenslackchat import zendesk_api


def test_zapi_client_default_config():
    """Verify the default Zenpy config env variables.
    """
    config = zendesk_api.config()    
    assert config['email'] == '<email@example.com>'
    assert config['token'] == '<token>'
    assert config['subdomain'] == '<something>'


def test_zapi_client_from_env_config(monkeypatch):
    """Verify the default Zenpy config env variables.
    """
    monkeypatch.setenv('ZENDESK_EMAIL', 'tony@example.com')
    monkeypatch.setenv('ZENDESK_TOKEN', 'token1234')
    monkeypatch.setenv('ZENDESK_SUBDOMAIN', 'helpsubdomain.example.com')
    
    config = zendesk_api.config()    
    assert config['email'] == 'tony@example.com'
    assert config['token'] == 'token1234'
    assert config['subdomain'] == 'helpsubdomain.example.com'


def test_zendesk_ticket_url(monkeypatch):
    """Verify the URL generated to point at (UI not API) ticket in zendesk.
    """
    monkeypatch.setenv(
        'ZENDESK_SUBDOMAIN', 
        'https://helpsubdomain.example.com/agent/tickets/'
    )

    url = zendesk_api.zendesk_ticket_url('ticket_id')
    assert url == 'https://helpsubdomain.example.com/agent/tickets/ticket_id'

    monkeypatch.setenv(
        'ZENDESK_SUBDOMAIN', 
        'https://helpsubdomain.example.com/agent/tickets'
    )

    url = zendesk_api.zendesk_ticket_url('17')
    assert url == 'https://helpsubdomain.example.com/agent/tickets/17'