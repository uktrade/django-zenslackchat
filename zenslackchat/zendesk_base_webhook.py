import pprint
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from webapp import settings
from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp


class BaseWebHook(APIView):
    """Handle Zendesk Events with authentication token.

    Zendesk will need to have a HTTP notifier and trigger configured to
    forward us comments.

    """
    def post(self, request, *args, **kwargs):
        """Handle the POSTed request from Zendesk.

        This will verify the shared token. If this not found or not as expected
        then 403 Forbidden will be raised.

        In all other situations the reponse 200 OK is returned. Any exceptions
        will be logged instead. This is to prevent Zendesk from think our end
        point is broken and not sending any further events.

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
                self.handle_event(
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

        except: # noqa: I'm logging rather than hidding.
            # I need to respond OK or I won't receive further events.
            log.exception('Failed handling webhook because:')

        return response

    def handle_event(self, event, slack_client, zendesk_client):
        """Over-ridden to implement event handling.

        :param event: The POSTed dict of fields.

        :param slack_client: Slack instance to use.

        :param zendesk_client: Zendesk instance to use.

        :returns: None

        """
