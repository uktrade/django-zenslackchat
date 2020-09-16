import logging
from datetime import timezone
from datetime import datetime

from django.db import models


def utcnow():
    return datetime.now(timezone.utc)


class NotFoundError(Exception):
    """Raised when a ZenSlackChat instance was not found."""


class Team(models.Model):
    """Used to store Slack OAuth client / bot details after successfull 
    completion of the OAuth process.

    """
    team_name = models.CharField(max_length=200)
    team_id = models.CharField(max_length=20)
    bot_user_id = models.CharField(max_length=20)
    bot_access_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=utcnow)


class ZendeskApp(models.Model):
    """Used to store Zendesk OAuth client / app details after successfull 
    completion of the OAuth process.
    
    """
    access_token = models.CharField(max_length=512)
    access_type = models.CharField(max_length=50)
    scopes = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=utcnow)


class ZenSlackChat(models.Model):
    """Represents data needed to manage conversations in Slack and sync this
    to and from Zendesk.

    The bot will only monitor active conversations. When an issue is resolved
    the conversation will be ignored.

    """
    # The channel which the slack message happening:
    # e.g. C019JUGAGTS
    channel_id = models.CharField(max_length=22)    

    # The slack message 'ts' that represent the conversation:
    # An epoch time e.g. 1597931771.007500
    chat_id = models.CharField(max_length=20)

    # The Zendesk Ticket ID:
    # e.g. 3451
    ticket_id = models.CharField(max_length=20)

    # Set to True if the chat bot is monitoring this chat:
    active = models.BooleanField(default=True)

    # Useful for metrics on chats open/closed per period of time.

    # When the chat was first opened.
    opened = models.DateTimeField(default=utcnow)

    # When the issue was resolved:
    closed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (('channel_id', 'chat_id'),)

    @classmethod
    def open(cls, channel_id, chat_id, ticket_id=None, opened=None):
        """Create a new issue for the chat bot to monitor.

        :param channel_id: The slack channel the conversation is in.

        :param chat_id: The conversation parent message identifier.

        :param ticket_id: The optional Zendesk Ticket ID.

        :param opened: The optional datetime (default is UTC now).

        :returns: A ZenSlackChat instance.

        """
        kwargs = dict(
            channel_id=channel_id,
            chat_id=chat_id,
            ticket_id=ticket_id
        )

        if opened:
            kwargs['opened'] = opened
        else:
            kwargs['opened'] = utcnow()

        issue = cls(**kwargs)
        issue.save()

        return issue

    @classmethod
    def get(cls, channel_id, chat_id):
        """Get a specific conversation.

        :param channel_id: The slack channel the conversation is in.

        :param chat_id: The conversation parent message identifier.

        :returns: A ZenSlackChat instance.
        
        If nothing is found for channel_id and chat_id then NotFoundError will
        be raised.

        """
        try:
            found = cls.objects.get(channel_id=channel_id, chat_id=chat_id)

        except cls.DoesNotExist:
            raise NotFoundError(
                f"Nothing found for channel_id:<{channel_id}> and "
                f"chat_id:<{chat_id}>"
            )

        return found

    @classmethod
    def get_by_ticket(cls, chat_id, ticket_id):
        """Get a specific conversation.

        :param chat_id: The conversation parent message identifier.

        :param ticket_id: The Zendesk Ticket ID.

        :returns: A ZenSlackChat instance.

        If nothing is found for chat_id and ticket_id then NotFoundError will
        be raised.
        
        """
        try:
            found = cls.objects.get(chat_id=chat_id, ticket_id=ticket_id)

        except cls.DoesNotExist:
            raise NotFoundError(
                f"Nothing found for chat_id:<{chat_id}> and "
                f"ticket_id:<{ticket_id}>"
            )

        return found

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
        issue = cls.get(channel_id, chat_id)

        issue.active = False
        if closed:
            issue.closed = closed
        else:
            issue.closed = utcnow()
        issue.save()

        return issue

    @classmethod
    def open_issues(cls):
        """Return a list of open issues the bot needs to monitor.

        I order by the most recently opened issue first. I reckoned the most
        recent needs the most attention.

        :returns: An empty list or list of ZenSlackChat instances.

        """
        return list(
            cls.objects.filter(active=True).order_by('-opened').all()
        )