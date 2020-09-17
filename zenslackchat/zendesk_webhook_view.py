import pprint
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from webapp import settings
from zenslackchat import message
from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp


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
        try:
            if settings.DEBUG:
                log.debug(f'Raw POSTed data:\n{pprint.pformat(request.data)}')

            message.update_with_comments_from_zendesk(
                request.data,
                slack_client=SlackApp.client(),
                zendesk_client=ZendeskApp.client()
            )

        except:
            log.exception(f'Failed handling webhook because:')

        return Response("Received OK, Thanks.", status=status.HTTP_200_OK)
