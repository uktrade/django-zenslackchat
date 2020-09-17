import json
import pprint
import logging

import requests
from django.conf import settings
from django.template import loader
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required

from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp


def slack_oauth(request):
    """Complete the OAuth process recovering the details needed to access the
    slack workspace we have just been added to.

    """
    log = logging.getLogger(__name__)

    if 'code' not in request.GET:
        log.error("The code parameter was missing in the request!")
        return Response(status=status.HTTP_400_BAD_REQUEST)

    code = request.GET['code']    
    log.debug(f"Received Slack OAuth request code:<{code}>")
    params = { 
        'code': code,
        'client_id': settings.SLACK_CLIENT_ID,
        'client_secret': settings.SLACK_CLIENT_SECRET
    }
    log.debug("Recovering access request from Slack...")
    json_response = requests.get(settings.SLACK_OAUTH_URI, params)
    log.debug(f"Result status from Slack:<{json_response.status_code}>")
    if settings.DEBUG:
        log.debug(f"Result from Slack:\n{json_response.text}")
    data = json.loads(json_response.text)

    SlackApp.objects.create(
        team_name=data['team_name'], 
        team_id=data['team_id'],
        bot_user_id=data['bot']['bot_user_id'],     
        bot_access_token=data['bot']['bot_access_token']
    )
    log.debug("Create local Team for this bot. Bot Added OK.")

    return HttpResponse('Bot added to your Slack team!')


def zendesk_oauth(request):
    """Complete the Zendesk OAuth process recovering the access_token needed to 
    perform API requests to the Zendesk Support API.

    """
    log = logging.getLogger(__name__)

    if 'code' not in request.GET:
        log.error("The code parameter was missing in the request!")
        return Response(status=status.HTTP_400_BAD_REQUEST)

    subdomain = settings.ZENDESK_SUBDOMAIN
    request_url = f"https://{subdomain}.zendesk.com/oauth/tokens"
    redirect_uri = settings.ZENDESK_REDIRECT_URI

    code = request.GET['code']    
    log.debug(
        f"Received Zendesk OAuth request code:<{code}>. "
        f"Recovering access token from {request_url}. "
        f"Redirect URL is {redirect_uri}. "
    )
    response = requests.post(
        request_url, 
        data=json.dumps({ 
            'code': code,
            'client_id': settings.ZENDESK_CLIENT_IDENTIFIER,
            'client_secret': settings.ZENDESK_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }),
        headers={"Content-Type": "application/json"}
    )
    log.debug(f"Result status from Zendesk:<{response.status_code}>")
    response.raise_for_status()
    data = response.json()
    log.debug(f"Result status from Zendesk:\n{pprint.pformat(data)}>")
    ZendeskApp.objects.create(
        access_token=data['access_token'], 
        token_type=data['token_type'], 
        scope=data['scope'], 
    )
    log.debug("Created local ZendeskApp instance OK.")

    return HttpResponse('ZendeskApp Added OK')


@login_required
def index(request):
    """A page Pingdom can log-in to test site uptime and DB readiness.
    """
    log = logging.getLogger(__name__)

    template = loader.get_template('zenslackchat/index.html')

    zendesk_oauth_request_uri = (
        "https://"
        f"{settings.ZENDESK_SUBDOMAIN}"
        ".zendesk.com/oauth/authorizations/new?"
        f"response_type=code&"
        f"redirect_uri={settings.ZENDESK_REDIRECT_URI}&"
        f"client_id={settings.ZENDESK_CLIENT_IDENTIFIER}&"
        "scope=read%20write"
    )
    log.debug(f"zendesk_oauth_request_uri:<{zendesk_oauth_request_uri}>")

    slack_oauth_request_uri = (
        "https://slack.com/oauth/authorize?"
        "scope=bot&"
        f"client_id={settings.SLACK_CLIENT_ID}"
    )
    log.debug(f"slack_oauth_request_uri:<{slack_oauth_request_uri}>")

    return HttpResponse(template.render(
        dict(
            zendesk_oauth_request_uri=zendesk_oauth_request_uri,
            slack_oauth_request_uri=slack_oauth_request_uri
        ), 
        request
    ))

    