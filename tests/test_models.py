import datetime

from django.test import TestCase
from zenslackchat.models import ZenSlackChat


class ModelTestCase(TestCase):
    def setUp(self):
        ZenSlackChat.open(
            channel_id="slack-channel-id-1", 
            chat_id="slack-chat-id-1", 
            ticket_id="zendesk-ticket-id-1", 
            created=datetime.datetime(2020, 1, 1, 12, 30)
        )
        ZenSlackChat.open(
            channel_id="slack-channel-id-2", 
            chat_id="slack-chat-id-2", 
            ticket_id="zendesk-ticket-id-2", 
            created=datetime.datetime(2020, 7, 17, 14, 0)
        )

    def test_basic_cru_functionality(self):
        """Test the basic operations we rely on.
        """
        self.assertEquals(ZenSlackChat.objects.count(), 2)

        chat1 = ZenSlackChat.get("slack-channel-id-1", "slack-chat-id-1")
        assert chat1.active is True
        assert chat1.closed is None
        assert chat1.created == datetime.datetime(2020, 1, 1, 12, 30)

        chat2 = ZenSlackChat.get("slack-channel-id-2", "slack-chat-id-2")
        assert chat2.active is True
        assert chat2.closed is None
        assert chat2.created == datetime.datetime(2020, 7, 17, 14, 0)

        results = ZenSlackChat.open_issues()
        assert len(results) == 2
        # The most recent issue should be first I've decided, check:
        assert results[0].created == datetime.datetime(2020, 7, 17, 14, 0)
        assert results[1].created == datetime.datetime(2020, 1, 1, 12, 30)

        ZenSlackChat.resolve(
            "slack-channel-id-1", 
            "slack-chat-id-1", 
            closed=datetime.datetime(2020, 8, 2, 9, 31)
        )

        results = ZenSlackChat.open_issues()
        assert len(results) == 1
        assert results[0].created == datetime.datetime(2020, 1, 1, 12, 30)

        chat1 = ZenSlackChat.get("slack-channel-id-1", "slack-chat-id-1")
        assert chat1.active is False
        assert chat1.closed == datetime.datetime(2020, 8, 2, 9, 31)
        assert chat1.created == datetime.datetime(2020, 1, 1, 12, 30)


