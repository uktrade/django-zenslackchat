from zenslackchat.zendesk_base_webhook import BaseWebHook
from zenslackchat.message import update_from_zendesk_email
from zenslackchat.message import update_with_comments_from_zendesk


class CommentsWebHook(BaseWebHook):
    """Handle Zendesk Comment Events.

    """    
    def handle_event(self, event, slack_client, zendesk_client):
        """Handle the comment trigger event we have been POSTed.

        Recover and update the comments with lastest from Zendesk.

        """
        update_with_comments_from_zendesk(event, slack_client, zendesk_client)


class EmailWebHook(BaseWebHook):
    """Handle Zendesk Email Events.

    """    
    def handle_event(self, event, slack_client, zendesk_client):
        """Handle the comment trigger event we have been POSTed.

        Recover and update the comments with lastest from Zendesk.

        """
        update_from_zendesk_email(event, slack_client, zendesk_client)
