import json
import logging

import requests
from django.conf import settings
from django.template import loader
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response

from zenslackchat.models import Team


def slack_oauth(request, url='https://slack.com/api/oauth.access'):
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
    json_response = requests.get(url, params)
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


def index(request):
    """Show the site root and button to add the bot to your slack workspace.
    """
    template = loader.get_template('zenslackchat/index.html')

    return HttpResponse(template.render(
        dict(client_id=settings.SLACK_CLIENT_ID), 
        request
    ))

    