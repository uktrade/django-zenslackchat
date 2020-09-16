import json
import logging

import requests
from django.conf import settings
from django.template import loader
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required

from zenslackchat.models import Team
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
    # log.debug(f"Result from Slack:\n{json_response.text}")
    data = json.loads(json_response.text)

    Team.objects.create(
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

    fqdn = settings.PAAS_FQDN
    redirect_url = f"https://{fqdn}/zendesk/oauth/"

    code = request.GET['code']    
    log.debug(f"Received Zendesk OAuth request code:<{code}>")
    params = { 
        'code': code,
        'client_id': settings.ZENDESK_CLIENT_IDENTIFIER,
        'client_secret': settings.ZENDESK_CLIENT_SECRET,
        'redirect_uri': redirect_url
    }
    log.debug("Recovering access request from Slack...")
    json_response = requests.get(request_url, params)
    log.debug(f"Result status from Zendesk:<{json_response.status_code}>")
    data = json.loads(json_response.text)

    ZendeskApp.objects.create(
        access_token=data['access_token'], 
        access_type=data['access_type'], 
        scopes=data['scopes'], 
    )
    log.debug("Created local ZendeskApp instance OK.")

    return HttpResponse('App added to your Zendesk.')


@login_required
def index(request):
    """A page Pingdom can log-in to test site uptime and DB readiness.
    """
    template = loader.get_template('zenslackchat/index.html')
    return HttpResponse(template.render({}, request))

    