# -*- coding: utf-8 -*-
import json
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from rest_framework.test import APIRequestFactory

from zenslackchat import views
from zenslackchat.models import PagerDutyApp, SlackApp, ZendeskApp


def test_slack_oauth_missing_code():
    """Test handling if no code is present in the request."""
    factory = APIRequestFactory()
    request = factory.get("/slack/oauth/")
    response = views.slack_oauth(request)
    assert response.status_code == 400


@patch("zenslackchat.views.settings")
@patch("zenslackchat.views.requests.get")
def test_slack_oauth_successful_token_exchange(requests_get, settings, log, db):
    """Test the ok path recoving the access token and creating the slack app
    instance.

    """
    # mock the OK response from Slack
    requests_get.return_value.status_code = 200
    requests_get.return_value.text = json.dumps(
        {
            "team_name": "super-team",
            "team_id": "team-abc-123",
            "bot": {
                "bot_user_id": "bot-user-id-123",
                "bot_access_token": "xoxob-123",
            },
        }
    )
    settings.SLACK_OAUTH_URI.return_value = "https://s.l.a.c.k"
    settings.SLACK_CLIENT_ID.return_value = "my-client-id"
    settings.SLACK_CLIENT_SECRET.return_value = "my-client-secret"

    factory = APIRequestFactory()
    request = factory.get("/slack/oauth/", dict(code=1234))
    response = views.slack_oauth(request)

    # Verify the response and the newly configured SlackApp instance:
    assert response.status_code == 200
    assert SlackApp.objects.count() == 1
    app = SlackApp.objects.first()
    assert app.team_name == "super-team"
    assert app.team_id == "team-abc-123"
    assert app.bot_user_id == "bot-user-id-123"
    assert app.bot_access_token == "xoxob-123"


def test_zendesk_oauth_missing_code():
    """Test handling if no code is present in the request."""
    factory = APIRequestFactory()
    request = factory.get("/zendesk/oauth/")
    response = views.zendesk_oauth(request)
    assert response.status_code == 400


@patch("zenslackchat.views.requests.post")
def test_zendesk_oauth_successful_token_exchange(requests_post, log, db):
    """Test the ok path recoving the access token and creating the zendesk app
    instance.

    """

    def loads():
        return {
            "access_token": "my-zd-access-token",
            "token_type": "bearer",
            "scope": "impersonate tickets:read tickets:write",
        }

    # mock the OK response from Zendesk
    requests_post.return_value.json = loads
    settings = dict(
        DEBUG=True,
        ZENDESK_SUBDOMAIN="bob_town",
        ZENDESK_REDIRECT_URI="https://my.app/oauth",
        ZENDESK_CLIENT_IDENTIFIER="my-client-id",
        ZENDESK_CLIENT_SECRET="my-client-secret",
    )

    factory = APIRequestFactory()
    request = factory.get("/zendesk/oauth/", dict(code=4321))
    with patch.dict("webapp.settings.__dict__", settings, clear=True):
        response = views.zendesk_oauth(request)

    # Verify the response and the newly configured ZendeskApp instance:
    assert response.status_code == 200
    assert ZendeskApp.objects.count() == 1
    app = ZendeskApp.objects.first()
    assert app.access_token == "my-zd-access-token"
    assert app.token_type == "bearer"
    assert app.scope == "impersonate tickets:read tickets:write"


# def test_pagerduty_oauth_missing_code():
#     """Test handling if no code is present in the request."""
#     factory = APIRequestFactory()
#     request = factory.get("/pagerduty/oauth/")
#     response = views.pagerduty_oauth(request)
#     assert response.status_code == 400


# @patch("zenslackchat.views.requests.post")
# def test_pagerduty_oauth_successful_token_exchange(requests_post, settings, log, db):
#     """Test the ok path recoving the access token and creating the PagerDuty
#     app instance.

#     """

#     def loads():
#         return {
#             "access_token": "my-pd-access-token",
#             "token_type": "bearer",
#             "scope": "read write",
#         }

#     # mock the OK response from PagerDuty
#     requests_post.return_value.json = loads
#     settings = dict(
#         DEBUG=True,
#         PD_TOKEN_END_POINT="bob_town",
#         PAGERDUTY_REDIRECT_URI="https://my.app/oauth",
#         PAGERDUTY_CLIENT_IDENTIFIER="my-client-id",
#         PAGERDUTY_CLIENT_SECRET="my-client-secret",
#     )

#     factory = APIRequestFactory()
#     request = factory.get("/pagerduty/oauth/", dict(code=9876, subdomain="frog"))
#     with patch.dict("webapp.settings.__dict__", settings, clear=True):
#         response = views.pagerduty_oauth(request)

#     # Verify the response and the newly configured PagerDutyApp instance:
#     assert response.status_code == 200
#     assert PagerDutyApp.objects.count() == 1
#     app = PagerDutyApp.objects.first()
#     assert app.access_token == "my-pd-access-token"
#     assert app.token_type == "bearer"
#     assert app.scope == "read write"
