import json
import datetime
from unittest.mock import patch
from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory, TestCase
from rest_framework.test import APIRequestFactory

from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat import zendesk_webhooks
from zenslackchat import zendesk_base_webhook
from zenslackchat.message import update_from_zendesk_email
from zenslackchat.message import update_with_comments_from_zendesk


def test_zendesk_request_is_rejected_with_missing_token_field():
    """Test if no token is present when data is POSTed to the 
    zendesk webhook webhook.

    """
    zendesk_event = {
        # no token in request
        # 'token': '...',
        'external_id': '1603983778.011500',
        'ticket_id': '1430',
    }
    factory = APIRequestFactory()
    view = zendesk_base_webhook.BaseWebHook.as_view()
    request = factory.post(
        '/zendesk/webhook/', 
        zendesk_event,
        format='json'
    )
    response = view(request)
    assert response.status_code == 403


def test_zendesk_request_token_is_incorrect():
    """Test that presenting the wrong token rejects the request.
    """
    zendesk_event = {
        'token': 'not-the-right-token',
        'external_id': '1603983778.011500',
        'ticket_id': '1430',
    }
    factory = APIRequestFactory()
    view = zendesk_base_webhook.BaseWebHook.as_view()
    request = factory.post(
        '/zendesk/webhook/', 
        zendesk_event,
        format='json'
    )
    override = {'ZENDESK_WEBHOOK_TOKEN': 'the-correct-token'}
    with patch.dict('webapp.settings.__dict__', override):    
        response = view(request)

    assert response.status_code == 403


@patch('zenslackchat.zendesk_base_webhook.SlackApp')
@patch('zenslackchat.zendesk_base_webhook.ZendeskApp')
@patch('zenslackchat.zendesk_webhooks.update_with_comments_from_zendesk')
def test_zendesk_exception_raised_by_update_comments(
    update_with_comments_from_zendesk, ZendeskApp, SlackApp, log, db
):
    """Test that 200 ok is returned even if update blows up internally.
    """
    zendesk_event = {
        'token': 'the-correct-token',
        'external_id': '1603983778.011500',
        'ticket_id': '1430',
    }
    factory = APIRequestFactory()
    view = zendesk_webhooks.CommentsWebHook.as_view()
    request = factory.post(
        '/zendesk/webhook/', 
        zendesk_event,
        format='json'
    )

    update_with_comments_from_zendesk.side_effect = ValueError(
        'fake problem occurred internally'
    )

    override = {'ZENDESK_WEBHOOK_TOKEN': 'the-correct-token'}
    with patch.dict('webapp.settings.__dict__', override):    
        response = view(request)

    assert response.status_code == 200
    update_with_comments_from_zendesk.assert_called()


@pytest.mark.parametrize(
    (
        'WebHookView', 'patch_path'
    ),
    (
        (
            zendesk_webhooks.EmailWebHook, 
            'zenslackchat.zendesk_webhooks.update_from_zendesk_email'
        ),
        (
            zendesk_webhooks.CommentsWebHook, 
            'zenslackchat.zendesk_webhooks.update_with_comments_from_zendesk'
        ),
    )
)
@patch('zenslackchat.zendesk_base_webhook.SlackApp')
@patch('zenslackchat.zendesk_base_webhook.ZendeskApp')
@patch('zenslackchat.zendesk_webhooks.update_from_zendesk_email')
def test_zendesk_webhook_events_ok_path(
    update_from_zendesk_email, ZendeskApp, SlackApp, 
    WebHookView, patch_path,
    log, db
):
    """Test OK cases for Zendesk webhooks.
    """
    class MockClient:
        def __init__(self, name):
            self.name = name

    SlackApp.client = MagicMock()
    slack_client = MockClient('slack')
    SlackApp.client.return_value = slack_client
    # test my understanding of who this should work
    assert SlackApp.client() == slack_client

    ZendeskApp.client = MagicMock()
    zendesk_client = MockClient('zendesk')
    ZendeskApp.client.return_value = zendesk_client
    assert ZendeskApp.client() == zendesk_client

    zendesk_event = {
        'token': 'the-correct-token',
        'ticket_id': '1430',
    }

    override = {'ZENDESK_WEBHOOK_TOKEN': 'the-correct-token'}

    with patch(patch_path) as expected_function_call:    
        with patch.dict('webapp.settings.__dict__', override):    
            view = WebHookView.as_view()
            factory = APIRequestFactory()
            request = factory.post(
                '/zendeskwebhook/', 
                zendesk_event,
                format='json'
            )
            response = view(request)

    assert response.status_code == 200
    SlackApp.client.assert_called()
    ZendeskApp.client.assert_called()
    expected_function_call.assert_called_with(
        zendesk_event,
        slack_client,
        zendesk_client
    )