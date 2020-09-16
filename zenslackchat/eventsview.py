import pprint
import logging

from slack import WebClient
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from zenslackchat import message


class Events(APIView):
    """Handle Events using the webapp instead of using the RTM API.

    This is handy as i don't need to run a specifc bot process just to handle
    events. Instead I can just using the webapp REST API for this.

    Handy documentation for Slack events: https://api.slack.com/events-api

    The app needs to subscribe to events to receive them. From 
    https://api.slack.com/apps/<APP ID>/event-subscriptions you need to:
    
    - Enable Events from "Off" to "On"
    - Enter the "Request URL" e.g.: http://<instance id>.ngrok.io/slack/events/
    - Then "Subscribe to events on behalf of users"
    - Click "Add Workspace Event" and add "message.channels".

    Message on channels will now start being recieved. The bot will need to be
    invited to a channel first.

    """    
    def post(self, request, *args, **kwargs):
        """Events will come in over a POST request.
        """
        log = logging.getLogger(__name__)

        slack_message = request.data

        if slack_message.get('token') != settings.SLACK_VERIFICATION_TOKEN:
            log.error("Slack message verification failed!")
            return Response(status=status.HTTP_403_FORBIDDEN)

        # verification challenge, convert to signature verification instead:
        if slack_message.get('type') == 'url_verification':
            return Response(data=slack_message, status=status.HTTP_200_OK)  

        if 'event' in slack_message:
            event = slack_message.get('event')
            try:
                # log.debug(f'event received:\n{pprint.pformat(event)}\n')
                message.handler(
                    event, 
                    our_channel=settings.SRE_SUPPORT_CHANNEL,
                    web_client=WebClient(
                        token=settings.SLACK_BOT_USER_TOKEN
                    )
                )
        
            except:
                log.exception("Slack message_handler error: ")

        return Response(status=status.HTTP_200_OK)
