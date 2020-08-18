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
