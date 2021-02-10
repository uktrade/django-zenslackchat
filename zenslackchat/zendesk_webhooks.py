from webapp import settings
from zenslackchat.zendesk_base_webhook import BaseWebHook
from zenslackchat.zendesk_email_to_slack import email_from_zendesk
from zenslackchat.zendesk_comments_to_slack import comments_from_zendesk


class CommentsWebHook(BaseWebHook):
    """Handle Zendesk Comment Events.
    """    
    def handle_event(self, event, slack_client, zendesk_client):
        """Handle the comment trigger event we have been POSTed.

        Recover and update the comments with lastest from Zendesk.

        """
        comments_from_zendesk(event, slack_client, zendesk_client)


class EmailWebHook(BaseWebHook):
    """Handle Zendesk Email Events.
    """    
    def handle_event(self, event, slack_client, zendesk_client):
        """Handle an email created issue and create it on slack.
        """
        email_from_zendesk(event, slack_client, zendesk_client)
