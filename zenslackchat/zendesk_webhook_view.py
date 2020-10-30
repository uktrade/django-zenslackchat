import base64
import pprint
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from webapp import settings
from zenslackchat import message
from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat.message import update_with_comments_from_zendesk


class WebHook(APIView):
    """Handle Zendesk Events.

    Zendesk will need to have a HTTP notifier and trigger configured to 
    forward us comments.

    """    
    def post(self, request, *args, **kwargs):
        """Handle the comment trigger event we have been POSTed.

        Recover and update the comments with lastest from Zendesk.

        """
        log = logging.getLogger(__name__)
        response = Response('OK, Thanks', status=200)

        if settings.DEBUG:
            log.debug(f'Raw POSTed data:\n{pprint.pformat(request.data)}')

        try:
            token = request.data.get(
                'token', '<token not set in webhook request body JSON>'
            )

            if token == settings.ZENDESK_WEBHOOK_TOKEN:
                update_with_comments_from_zendesk(
                    request.data,
                    slack_client=SlackApp.client(),
                    zendesk_client=ZendeskApp.client()
                )
            
            else:
                log.error(
                    'Webhook JSON body token does no match expected token '
                    'settings.ZENDESK_WEBHOOK_TOKEN token.'
                )

                if settings.DEBUG:
                    log.debug(
                        f"Webhook rejected as token '{token}' does not "
                        f"match ours '{settings.ZENDESK_WEBHOOK_TOKEN}'"
                    )

                response = Response(status=status.HTTP_403_FORBIDDEN)

        except:
            log.exception(f'Failed handling webhook because:')

        return response
