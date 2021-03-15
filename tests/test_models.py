import datetime
from unittest.mock import patch
from unittest.mock import MagicMock

import pytest
from django.test import TestCase

from zenslackchat.models import ZenSlackChat
from zenslackchat.models import NotFoundError
from zenslackchat.models import OutOfHoursInformation


UTC = datetime.timezone.utc


@pytest.mark.parametrize(
    ('now', 'expected'),
    [
        # office hours range 09:00 - 17:00.
        (datetime.datetime(2021, 3, 9, 9, 0, 0, tzinfo=UTC), False),
        (datetime.datetime(2021, 3, 9, 15, 34, 12, tzinfo=UTC), False),
        (datetime.datetime(2021, 3, 9, 17, 0, 0, tzinfo=UTC), False),
        # Outside range is out of hours:
        (datetime.datetime(2021, 3, 9, 8, 59, 59, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 9, 17, 0, 1, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 9, 22, 40, 2, tzinfo=UTC), True),
        # weekend is oo:
        (datetime.datetime(2021, 3, 13, 9, 0, 0, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 14, 17, 0, 0, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 7, 8, 59, 59, tzinfo=UTC), True),
]
)
@patch('zenslackchat.models.post_message')
def test_inform_if_out_of_hours(post_message, log, db, now, expected):
    """Verify when an out of hours message is 'posted' to slack.
    """
    slack_client = MagicMock()

    OutOfHoursInformation.update("Contact XYZ", hours=("09:00", "17:00"))

    assert OutOfHoursInformation.inform_if_out_of_hours(
        now,
        chat_id='some-chat-id',
        channel_id='A0192KL3TFG',
        slack_client=slack_client
    ) == expected

    if expected is True:
        post_message.assert_called_with(
            slack_client,
            'some-chat-id',
            'A0192KL3TFG',
            "Contact XYZ"
        )

    else:
        post_message.assert_not_called()


@pytest.mark.parametrize(
    ('now', 'expected'),
    [
        # office hours range 09:00 - 17:00.
        (datetime.datetime(2021, 3, 9, 9, 0, 0, tzinfo=UTC), False),
        (datetime.datetime(2021, 3, 9, 15, 34, 12, tzinfo=UTC), False),
        (datetime.datetime(2021, 3, 9, 17, 0, 0, tzinfo=UTC), False),
        # Outside range is out of hours:
        (datetime.datetime(2021, 3, 9, 8, 59, 59, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 9, 17, 0, 1, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 9, 22, 40, 2, tzinfo=UTC), True),
        # Weekend is out of hours:
        # saturday
        (datetime.datetime(2021, 3, 13, 9, 0, 0, tzinfo=UTC), True),
        # sunday
        (datetime.datetime(2021, 3, 14, 17, 0, 0, tzinfo=UTC), True),
        (datetime.datetime(2021, 3, 7, 8, 59, 59, tzinfo=UTC), True),
    ]
)
def test_is_out_of_hours_with_default(log, db, now, expected):
    """Test the logic for working out if a time is in or out of working hours.
    """
    OutOfHoursInformation.update(hours=("09:00", "17:00"))
    assert OutOfHoursInformation.is_out_of_hours(now) == expected


def test_out_of_hours_information(log, db):
    """Test default and help text recovery.
    """
    # Test the default with not text set
    message = OutOfHoursInformation.help_text()
    assert message == 'No Out Of Hours Message Set!'

    OutOfHoursInformation.update("""
Contact a@b.com
Modile: +44 123456
    """)

    message = OutOfHoursInformation.help_text()
    assert message == """
Contact a@b.com
Modile: +44 123456
    """


def test_out_of_hours_instance(log, db):
    """Test default and help text recovery.
    """
    OutOfHoursInformation.update()

    oohi = OutOfHoursInformation.help()
    assert oohi.message == 'No Out Of Hours Message Set!'
    assert oohi.office_hours_begin == datetime.time(9, 0)
    assert oohi.office_hours_end == datetime.time(17, 0)

    oohi2 = OutOfHoursInformation.update(
        "Contact XYZ",
        ("09:30", "18:30")
    )
    assert oohi2.message == 'Contact XYZ'
    assert oohi2.office_hours_begin == datetime.time(9, 30)
    assert oohi2.office_hours_end == datetime.time(18, 30)


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
