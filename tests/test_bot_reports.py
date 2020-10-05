import datetime

import pytest
from django.test import TestCase

from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError


UTC = datetime.timezone.utc


ISSUE_FIXTURES = [
    # Old open issue on 31 Dec 2019
    dict(
        chat_id="slack-chat-0", 
        ticket_id="zendesk-ticket-0", 
        opened=datetime.datetime(2019, 12, 28, 13, 51, tzinfo=UTC),
        closed=None,
    ),

    # On 1st Jan 2020
    #
    # Two closed issues 
    # Three open issues
    #
    # closed on 1 Jan 2020
    dict(
        chat_id="slack-chat-1", 
        ticket_id="zendesk-ticket-1", 
        opened=datetime.datetime(2020, 1, 1, 12, 30, tzinfo=UTC),
        closed=datetime.datetime(2020, 1, 1, 13, 42, tzinfo=UTC),
    ),
    dict(
        chat_id="slack-chat-2", 
        ticket_id="zendesk-ticket-2", 
        opened=datetime.datetime(2020, 1, 1, 12, 30, tzinfo=UTC),
        closed=datetime.datetime(2020, 1, 1, 17, 11, tzinfo=UTC),
    ),
    # open 1 Jan 2020
    dict(
        chat_id="slack-chat-3", 
        ticket_id="zendesk-ticket-3", 
        opened=datetime.datetime(2020, 1, 1, 8, 7, tzinfo=UTC),
        closed=None
    ),
    dict(
        chat_id="slack-chat-4", 
        ticket_id="zendesk-ticket-4", 
        opened=datetime.datetime(2020, 1, 1, 22, 44, tzinfo=UTC),
        closed=None
    ),
    dict(
        chat_id="slack-chat-5", 
        ticket_id="zendesk-ticket-5", 
        opened=datetime.datetime(2020, 1, 1, 12, 30, tzinfo=UTC),
        closed=None
    )
]


def test_daily_summary_data(log, db):
    """Test the output of the daily report.
    """
    workspace_uri = 'https://s.l.a.c.k'

    # Generate fixtures for report run:
    for issue in ISSUE_FIXTURES:
        ZenSlackChat.open(
            channel_id='some_channel_id', 
            chat_id=issue['chat_id'], 
            ticket_id=issue['ticket_id'], 
            opened=issue['opened']
        )
        if issue['closed']:
            ZenSlackChat.resolve(
                channel_id='some_channel_id', 
                chat_id=issue['chat_id'], 
                closed=issue['closed']
            )

    # Its the 2 Jan 2020, report on what happened on 1 Jan. This should count
    # all open issues, but only count closed issues for 1 Jan.
    #
    now = datetime.datetime(2020, 1, 2, 0, 0, 0, tzinfo=UTC)

    report  = ZenSlackChat.daily_summary(workspace_uri, when=now)

    # 3 on 1 Jan + 1 still open on 31 Dec:
    assert len(report['open']) == 4

    # oldest issue first
    assert report['open'][0] == (
        'https://s.l.a.c.k/some_channel_id/pzendesk-ticket-4'
    )

    # Only the 2 closed issues on 1 Jan:
    assert report['closed'] == 2

    # Its the 3 Jan 2020, report on what happened on 2 Jan.
    #
    now = datetime.datetime(2020, 1, 3, 0, 0, 0, tzinfo=UTC)

    report  = ZenSlackChat.daily_summary(workspace_uri, when=now)

    # 3 on 1 Jan + 1 still open on 31 Dec:
    assert len(report['open']) == 4

    # No closed issues on 2 Jan:
    assert report['closed'] == 0


def test_daily_report_plaintext(log, db):
    """Test the text output that could be sent as a daily report.
    """
    report = dict(
        open=[
            "https://s.l.a.c.k/chat-id-1", 
            "https://s.l.a.c.k/chat-id-2", 
            "https://s.l.a.c.k/chat-id-3", 
            "https://s.l.a.c.k/chat-id-4", 
        ],
        closed=3
    )

    plain_text  = ZenSlackChat.daily_report(report)

    expected = """
📊 Daily WebOps SRE Issue Report

Closed 🤘: 3

Unresolved 🔥: 4
- https://s.l.a.c.k/chat-id-1
- https://s.l.a.c.k/chat-id-2
- https://s.l.a.c.k/chat-id-3
- https://s.l.a.c.k/chat-id-4

Cheers,

🤖 ZenSlackChat
    """.strip()

    assert plain_text == expected    