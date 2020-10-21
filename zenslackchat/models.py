import logging
from datetime import timezone
from datetime import datetime
from datetime import timedelta

from zenpy import Zenpy
from slack import WebClient
from django.db import models

from webapp import settings
from zenslackchat import slack_api


def utcnow():
    return datetime.now(timezone.utc)


class NotFoundError(Exception):
    """Raised when a ZenSlackChat instance was not found."""


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

    # The ID of the linked issue in Zendesk:
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

    @classmethod
    def daily_summary(cls, workspace_uri, when=None):
        """Generate the data for the daily report.

        :param workspace_uri: The base URI for messages on slack.

        :param when: None or UTC datetime instance for 'today'.

        Used to work yesterday's date. All open tickets are counted and not 
        just those for the yesterday. Only yesterday's closed tickets on are 
        counted.

        :returns: A dict(open=[..links to slack issues..], closed=<a count>)

        """
        if when:
            yesterday = when - timedelta(days=1)

        else:
            yesterday = utcnow() - timedelta(days=1)

        day_begin = datetime(
            yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, 0,
            tzinfo=timezone.utc
        )

        day_end = datetime(
            yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, 999,
            tzinfo=timezone.utc
        )

        returned = dict(open=[], closed=0)

        for issue in cls.open_issues():
            returned['open'].append(slack_api.message_url(
                workspace_uri,
                issue.channel_id, 
                issue.chat_id, 
            ))

        returned['closed'] = cls.objects.filter(
            closed__range=(day_begin, day_end)
        ).count()

        return returned

    @classmethod
    def daily_report(cls, report):
        """Generate the daily report text for the given report.

        :param report: The result of a cls.daily_summary call().

        :returns: A plain text report that could be sent to interested parties.

        """
        closed = report['closed']

        open = len(report['open'])

        links = []
        for link in report['open']:
            links.append(f"- {link}")
        links = "\n".join(links)

        report = f"""
📊 Daily WebOps SRE Issue Report

Closed 🤘: {closed}

Unresolved 🔥: {open}
{links}

Cheers,

🤖 ZenSlackChat
        """.strip()

        return report 


class SlackApp(models.Model):
    """Used to store Slack OAuth client / bot details after successfull 
    completion of the OAuth process.

    """
    team_name = models.CharField(max_length=200)
    team_id = models.CharField(max_length=20)
    bot_user_id = models.CharField(max_length=20)
    bot_access_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=utcnow)

    @classmethod
    def client(cls):
        """Returns a Slack web client ready for use.

        This recovers the latest SlackApp instance and uses its 
        bot_access_token field for the web client.

        """
        # use the latest token
        app = cls.objects.order_by('-created_at').first()
        if settings.DEBUG:
            logging.getLogger(__name__).debug(
                f"Bot Access Token:{app.bot_access_token}"
            )

        return WebClient(token=app.bot_access_token)


class ZendeskApp(models.Model):
    """Used to store Zendesk OAuth client / app details after successfull 
    completion of the OAuth process.
    
    """
    access_token = models.CharField(max_length=512)
    token_type = models.CharField(max_length=50)
    scope = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=utcnow)

    @classmethod
    def client(cls):
        """Returns a Zenpy client instance ready for use.

        This recovers the latest ZendeskApp instance and uses its access_token
        field for the token.

        """
        # use the latest token
        app = cls.objects.order_by('-created_at').first()
        if settings.DEBUG:
            logging.getLogger(__name__).debug(
                f"Zendesk Access Token:{app.access_token}"
            )

        return Zenpy(
            subdomain=settings.ZENDESK_SUBDOMAIN,
            oauth_token=app.access_token
        )
