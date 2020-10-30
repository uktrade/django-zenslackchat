import json
import datetime
from unittest.mock import patch
from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from zenslackchat import views
from zenslackchat import eventsview


@patch('zenslackchat.eventsview.handler')
def test_request_is_rejected_with_missing_token_field(handler):
    """Test 403 Forbidden if no token is present when data is POSTed to the 
    event webhook.

    """
    factory = APIRequestFactory()
    slack_event = {
        'channel': 'C0192NP3TFG',
        'channel_type': 'channel',
        'client_msg_id': '49d75d96-1a73-4564-8970-29020156e5d2',
        'event_ts': '1603983778.011500',
        'team': 'TGFJG8VEZ',
        'text': 'hello there!',
        'thread_ts': '1603982476.010000',
        'ts': '1603983778.011500',
        'type': 'message',
        'user': 'UGF7MRWMS'
    }

    events_view = eventsview.Events.as_view()
    request = factory.post(
        '/slack/events/', 
        dict(event=slack_event),
        format='json'
    )
    response = events_view(request)
    # Forbidden
    assert response.status_code == 403
    # this should not have been called.
    handler.assert_not_called()