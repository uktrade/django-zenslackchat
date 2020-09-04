import logging
from datetime import datetime

from django.db import models


class ZenSlackChat(models.Model):
    """Represents data needed to manage conversations in Slack and sync this
    to and from Zendesk.

    The bot will only monitor active conversations. When an issue is resolved
    the conversation will be ignored.

    """
    class Meta:
        unique_together = (('channel_id', 'chat_id'),)

    # The channel which the slack message happening:
    # e.g. C019JUGAGTS
    channel_id = models.CharField(max_length=22)    

    # The slack message 'ts' that represent the conversation:
    # An epoch time e.g. 1597931771.007500
    chat_id = models.CharField(max_length=20)

    # The Zendesk Ticket ID:
    # e.g. 3451
    ticket_id = models.CharField(max_length=10)

    # Set to True if the chat bot is monitoring this chat:
    active = models.BooleanField(default=True)

    # Useful for metrics on chats open/closed per period of time.

    # When the chat was first opened.
    opened = models.DateTimeField(default=datetime.utcnow)

    # When the issue was resolved:
    closed = models.DateTimeField(default=datetime.utcnow)

    @classmethod
    def open(cls, channel_id, chat_id, ticket_id=None, created=None):
        """Create a new issue for the chat bot to monitor.

        :param channel_id: The slack channel the conversation is in.

        :param chat_id: The conversation parent message identifier.

        :param ticket_id: The optional Zendesk Ticket ID.

        :param created: The optional datetime (default is UTC now).

        :returns: A ZenSlackChat instance.

        """

    @classmethod
    def get(cls, channel_id, chat_id):
        """Get a specific conversation.

        :param channel_id: The slack channel the conversation is in.

        :param chat_id: The conversation parent message identifier.

        :returns: A ZenSlackChat instance or None.
        
        """

    @classmethod
    def resolve(cls, channel_id, chat_id, closed=None):
        """Close the issue and stop the bot monitoring this chat.

        :param channel_id: The slack channel the conversation is in.

        :param chat_id: The conversation parent message identifier.

        :param closed: The optional datetime (default is UTC now).

        :returns: The resolved ZenSlackChat instance.

        The active flag will be cleared and the closed timestamp set. The bot
        should stop monitoring this chat.

        """

    @classmethod
    def open_issues(cls):
        """Return a list of open issues the bot needs to monitor.

        :returns: An empty list or list of ZenSlackChat instances.

        """
