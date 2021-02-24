from datetime import datetime
from datetime import timezone
from unittest.mock import patch
from unittest.mock import MagicMock

import pytest

from zenslackchat import message_tools
from zenslackchat.models import PagerDutyApp
from zenslackchat.message_tools import is_resolved
from zenslackchat.message_tools import messages_for_slack
from zenslackchat.message_tools import message_who_is_on_call
from zenslackchat.message_tools import message_issue_zendesk_url


UTC = timezone.utc


def _utc(dt):
    return dt.replace(tzinfo=UTC)


@pytest.mark.parametrize(
    ('resolve_command', 'expected'),
    [
        ('resolve ticket', True),
        ('resolve', True),
        ('✅', True),
        ('🆗', True),
        ('Yo!', False),
        ('res', False),
        ('stfu', False),
        ('resolv', False),
    ]
)
def test_is_resolve(resolve_command, expected):
    assert is_resolved(resolve_command) is expected


@patch('zenslackchat.message_tools.post_message')
def test_message_issue_zendesk_url_tools(post_message, db, log):
    """Test slack message for the zendesk issue link.
    """
    channel_id = 'slack-channel-id'
    chat_id = 'slack-chat-id'
    ticket_id = 'ticket-id'
    slack_client = MagicMock()
    zendesk_uri = 'https://z.e.n.d.e.s.k/'

    message_issue_zendesk_url(
        slack_client, zendesk_uri, ticket_id, chat_id, channel_id
    )
    
    # Verify the what should be sent to slack:
    post_message.assert_called_with(
        slack_client,
        'slack-chat-id',
        'slack-channel-id',
        'Hello, your new support request is https://z.e.n.d.e.s.k/ticket-id'
    )


@patch('zenslackchat.message_tools.post_message')
@patch('zenslackchat.models.APISession.get')
def test_message_who_is_on_call(session_get, post_message, db, log):
    """Test the message sent / not sent for who is on call.
    """
    channel_id = 'slack-channel-id'
    chat_id = 'slack-chat-id'
    slack_client = MagicMock()

    # With no PagerDutyApp set up then no message should be sent:
    message_who_is_on_call(
        PagerDutyApp.on_call(), slack_client, chat_id, channel_id
    )
    post_message.assert_not_called()    
    post_message.reset_mock()

    # Configure PageDurty and test the message sent:
    pd = PagerDutyApp(
        access_token='my-access-token',
        token_type='my-token-type',
        scope='my scopes for the token type'
    )
    pd.save()

    # Mock the PagerDuty requests.get call recovering who is on call:
    def loads():
        # Representative of what PagerDuty returns
        return {"oncalls": [
            {
                "escalation_policy": {
                    "id": "my-policy-id",
                    "type": "escalation_policy_reference",
                    "summary": "Silver P1",
                    "self": "https://api/escalation_policies/my-policy-id",
                    "html_url": "https://etc/escalation_policies/my-policy-id"
                },
                "escalation_level": 1,
                "schedule": {
                    "id": "schedule-id",
                    "type": "schedule_reference",
                    "summary": "Extended Hours - Primary",
                    "self": "https://api/schedules/schedule-id",
                    "html_url": "https://etc/schedules/schedule-id"
                },
                "user": {
                    "id": "user-id-1",
                    "type": "user_reference",
                    "summary": "Fred Sprocket",
                    "self": "https://api...etc",
                    "html_url": "https://uktrade...etc"
                },
                "start": "2020-12-03T08:00:00Z",
                "end": "2020-12-03T22:00:00Z"
            },
            {
                "escalation_policy": {
                    "id": "my-policy-id",
                    "type": "escalation_policy_reference",
                    "summary": "Silver P1",
                    "self": "https://api/escalation_policies/my-policy-id",
                    "html_url": "https://etc/escalation_policies/my-policy-id"
                },
                "escalation_level": 2,
                "schedule": {
                    "id": "schedule-id-2",
                    "type": "schedule_reference",
                    "summary": "Extended Hours - Secondary",
                    "self": "https://api/schedules/schedule-id-2",
                    "html_url": "https://etc/schedules/schedule-id-2"
                },
                "user": {
                    "id": "user-id-2",
                    "type": "user_reference",
                    "summary": "Tony Tiger",
                    "self": "https://api...etc",
                    "html_url": "https://uktrade...etc"
                },
                "start": "2020-12-02T08:00:00Z",
                "end": "2020-12-02T22:00:00Z"
            }
        ],
        "limit": 25,
        "offset": 0,
        "more": False,
        "total": None
    }
    session_get.return_value.json = loads
    message = (
        "📧 Primary on call: Fred Sprocket\n"
        "ℹ️ Secondary on call: Tony Tiger."
    )
    message_who_is_on_call(
        PagerDutyApp.on_call(), slack_client, chat_id, channel_id
    )

    # Verify the what should be sent to slack:
    post_message.assert_called_with(
        slack_client,
        'slack-chat-id',
        'slack-channel-id',
        message
    )    


@pytest.mark.parametrize(
    ('epoch', 'expected'),
    [
        ('1598459584.013100', _utc(datetime(2020, 8, 26, 16, 33, 4))),
        (1598459584.013100, _utc(datetime(2020, 8, 26, 16, 33, 4))),
        (1608215929, _utc(datetime(2020, 12, 17, 14, 38, 49))),
        ('1608215929', _utc(datetime(2020, 12, 17, 14, 38, 49)))
    ]
)
def test_ts_to_datetime(epoch, expected):
    assert message_tools.ts_to_datetime(epoch) == expected


@pytest.mark.parametrize(
    ('iso8601_str', 'expected'),
    [
        (
            '2020-09-08T16:35:14Z', 
            _utc(datetime(2020, 9, 8, 16, 35, 14))
        ),
    ]
)
def test_utc_to_datetime(iso8601_str, expected):
    assert message_tools.utc_to_datetime(iso8601_str) == expected


@pytest.mark.parametrize(
    ('signature', 'expected'),
    [
        (
            "", ""
        ),
        (
            """
email body of subject 111

-- 

Oisin Mulvihill | Webops/SRE | Digital
Department for International Trade | 50 Victoria Street, London SW1E 5LB | 
E-mail: ..

Communications with the Department for International Trade may be automatically 
logged, monitored and/or recorded for legal purposes.
""", 
            # newline before -- kept
            """
email body of subject 111

"""
        ),
    ]
)
def test_strip_signature_from_subject(signature, expected):
    result = message_tools.strip_signature_from_subject(signature)
    assert result == expected


def test_new_message_for_slack_is_detected(log):
    """Regression test: the comparisson between slack and zendesk messasges 
    was failing. Slack uses the emoji name and zendesk using the emoji 
    character.

    This was causing message from zendesk to be repeatedly added to slack as 
    they appeared to be new messages.

    """
    # The fixture data is not complete just the fields I'm using to recreate
    # the bug
    zendesk = [
        {'body': 'This is the message on slack <link>.',
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=UTC),
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'body': '👍',
        'created_at': datetime(2020, 9, 9, 17, 8, 14, tzinfo=UTC),
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
    ]

    slack = [
        {'created_at': datetime(2020, 9, 9, 16, 10, 26, tzinfo=UTC),
        'text': ':fish:',
        'thread_ts': '1599667826.017500',
        'ts': '1599667826.017500',
        'type': 'message',
        'user': 'UGF7MRWMS'},
        {'bot_id': 'B01ADD673UL',
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=UTC),
        'text': 'Hello, your new support request is <link>',
        'thread_ts': '1599667826.017500',
        'ts': '1599667829.017600',
        'type': 'message',
        'user': 'U01AKS3HDJ5'}
    ]    

    results = messages_for_slack(slack, zendesk)

    # The thumbs up message is new so it should be added to slack here:
    assert len(results) == 1
    assert results[0]['body'] == '👍'


@pytest.mark.parametrize(
    ('email_body', 'truncated', 'character_limit'),
    [
        # The message characters including whitespace is longer that 4 so 
        # will result in ... indicating truncation.
        (
            r"""1
2
3
4
5
6
7
8
""",
            "1\n2\n...",
            4
        ),
        # All message fits in 16 characters so ... won't appear:
        (
            "1\n2\n3\n4\n5\n6\n7\n8\n",
            "1\n2\n3\n4\n5\n6\n7\n8\n",
            16
        ),
        (
            """Dear Webops,

Could you please add Person into XYZ User Group on Jira? 

Thank you,

--

Name

Department for International Trade 

            """.strip(),
            """Dear Webops,

Could you please add Person into XYZ User Group on Jira?...""",
            70
        )
    ]
)
def test_truncate_email(email_body, truncated, character_limit):
    assert message_tools.truncate_email(
        email_body, character_limit
    ) == truncated


def test_markdown_links_correctly_stripped(log):
    """Test only four lines of the email body are use as a summary
    """
    text = "<http://QUAY.IO|QUAY.IO> MICRO PLAN"
    cleaned = "QUAY.IO MICRO PLAN"
    assert message_tools.strip_formatting(text) == cleaned

    text = "<https://QUAY.IO|QUAY.IO> MICRO PLAN"
    cleaned = "QUAY.IO MICRO PLAN"
    assert message_tools.strip_formatting(text) == cleaned

    text = "<https://QUAY.IO> MICRO PLAN"
    cleaned = "QUAY.IO MICRO PLAN"
    assert message_tools.strip_formatting(text) == cleaned
