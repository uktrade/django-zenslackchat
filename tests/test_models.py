import datetime

import pytest
from django.test import TestCase

from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError


UTC = datetime.timezone.utc


def test_basic_cru_functionality(log, db):
    """Test the basic operations we rely on.
    """
    ZenSlackChat.open(
        channel_id="slack-channel-id-1", 
        chat_id="slack-chat-id-1", 
        ticket_id="zendesk-ticket-id-1", 
        opened=datetime.datetime(2020, 1, 1, 12, 30, tzinfo=UTC)
    )

    ZenSlackChat.open(
        channel_id="slack-channel-id-2", 
        chat_id="slack-chat-id-2", 
        ticket_id="zendesk-ticket-id-2", 
        opened=datetime.datetime(2020, 7, 17, 14, 0, tzinfo=UTC)
    )

    assert ZenSlackChat.objects.count() == 2

    chat1 = ZenSlackChat.get("slack-channel-id-1", "slack-chat-id-1")
    assert chat1.active is True
    assert chat1.closed is None
    assert chat1.opened == datetime.datetime(
        2020, 1, 1, 12, 30, tzinfo=UTC
    )

    chat2 = ZenSlackChat.get("slack-channel-id-2", "slack-chat-id-2")
    assert chat2.active is True
    assert chat2.closed is None
    assert chat2.opened == datetime.datetime(
        2020, 7, 17, 14, 0, tzinfo=UTC
    )

    results = ZenSlackChat.open_issues()
    assert len(results) == 2
    # The most recent issue should be first I've decided, check:
    assert results[0].opened == datetime.datetime(
        2020, 7, 17, 14, 0, tzinfo=UTC
    )
    assert results[1].opened == datetime.datetime(
        2020, 1, 1, 12, 30, tzinfo=UTC
    )

    ZenSlackChat.resolve(
        "slack-channel-id-1", 
        "slack-chat-id-1", 
        closed=datetime.datetime(2020, 8, 2, 9, 31, tzinfo=UTC)
    )

    results = ZenSlackChat.open_issues()
    assert len(results) == 1
    assert results[0].opened == datetime.datetime(
        2020, 7, 17, 14, 0, tzinfo=UTC
    )

    chat1 = ZenSlackChat.get("slack-channel-id-1", "slack-chat-id-1")
    assert chat1.active is False
    assert chat1.closed == datetime.datetime(2020, 8, 2, 9, 31, tzinfo=UTC)
    assert chat1.opened == datetime.datetime(2020, 1, 1, 12, 30, tzinfo=UTC)


def test_not_found(db):
    """Verify how I handle not finding instances.
    """
    with pytest.raises(NotFoundError):
        ZenSlackChat.get("slack-channel-id-1", "slack-chat-id-1")

    with pytest.raises(NotFoundError):
        ZenSlackChat.get_by_ticket("slack-chat-id-1", "zendesk-ticket-id-1")

    with pytest.raises(NotFoundError):
        ZenSlackChat.resolve("slack-channel-id-1", "slack-chat-id-1")


def test_no_open_issues(db):
    """Verify I get no open issues when DB is empty.
    """
    assert ZenSlackChat.open_issues() == []
