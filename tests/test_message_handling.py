from unittest.mock import patch
from unittest.mock import MagicMock

import pytest

from zenslackchat.message import handler
from zenslackchat.models import PagerDutyApp
from zenslackchat.message import is_resolved
from zenslackchat.models import ZendeskApp
from zenslackchat.models import ZenSlackChat
from zenslackchat.message import IGNORED_SUBTYPES
from zenslackchat.message import message_who_is_on_call
from zenslackchat.message import message_issue_zendesk_url
from zenslackchat.message import update_from_zendesk_email


class FakeTicket(object):
    def __init__(self, ticket_id, subject='', description=''):
        self.id = ticket_id
        self.status = 'open'
        self.subject = subject
        self.description = description


class FakeUserResponse(object):
    def __init__(self):
        self.data = dict(
            user=dict(
                real_name='Bob Sprocket',
                profile=dict(
                    email='bob@example.com'
                )
            )
        )


@patch('zenslackchat.message.post_message')
def test_message_issue_zendesk_url(post_message, db, log):
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


@patch('zenslackchat.message.post_message')
@patch('zenslackchat.models.APISession.get')
def test_message_who_is_on_call(session_get, post_message, db, log):
    """Test the message sent / not sent for who is on call.
    """
    channel_id = 'slack-channel-id'
    chat_id = 'slack-chat-id'
    slack_client = MagicMock()

    # With no PagerDutyApp set up then no message should be sent:
    message_who_is_on_call(slack_client, chat_id, channel_id)
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
    settings = dict(DEBUG=True, PAGERDUTY_ESCALATION_POLICY_ID='my-policy-id')
    message = (
        "📧 Primary on call: Fred Sprocket\n"
        "ℹ️ Secondary on call: Tony Tiger."
    )
    with patch.dict('webapp.settings.__dict__', settings, clear=True):
        message_who_is_on_call(slack_client, chat_id, channel_id)

    # Verify the what should be sent to slack:
    post_message.assert_called_with(
        slack_client,
        'slack-chat-id',
        'slack-channel-id',
        message
    )


@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.post_message')
@patch('zenslackchat.message.SlackApp')
@patch('zenslackchat.message.ZendeskApp')
def test_email_from_zendesk_is_added_for_tracking(
    ZendeskApp, SlackApp, post_message, get_ticket, log, db
):
    """Test linking an email created issue into our DB for tracking.
    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    chat_id = '1597940362.013100'
    channel_id = 'C024JUTACTS'
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'

    slack_client.users_info.return_value = FakeUserResponse()
    slack_client.chat_postMessage.return_value = {
        'message': {
            'ts': chat_id
        }
    }
    SlackApp.client.return_value = slack_client

    # Return out fake ticket when asked to create:
    get_ticket.return_value = FakeTicket(
        ticket_id='32',
        subject='My printer is on 🔥',
        description='I was smoking next to it and it just went up.'
    )

    # Return out fake ticket when asked to create:
    class ZendeskMe:
        id = 'zendesk-user-id'
    zendesk_client.users.me.return_value = ZendeskMe()
    ZendeskApp.client.return_value = zendesk_client

    # There should be no entries here yet:
    assert ZenSlackChat.objects.count() == 0

    # Zendesk has a new support request via email. Update our system 
    # to start tracking this.
    #
    # The EmailWebHook.handle_event will add in the extra keys that 
    # update_from_zendesk_email will need.
    event = {
        'ticket_id': '32',
        # EmailWebHook.handle_event adds these to the event before calling:
        'channel_id': channel_id,
        'zendesk_uri': zendesk_uri,
        'workspace_uri': workspace_uri
    }
    update_from_zendesk_email(event, slack_client, zendesk_client)

    # There should now be one instance here:
    assert ZenSlackChat.objects.count() == 1
    assert len(ZenSlackChat.open_issues()) == 1

    # Verify what the stored issue should look like:
    issue = ZenSlackChat.get('C024JUTACTS', '1597940362.013100')
    assert issue.active is True
    assert issue.opened is not None
    assert issue.closed is None
    assert issue.channel_id == 'C024JUTACTS'
    assert issue.chat_id == '1597940362.013100'
    assert issue.ticket_id == '32'


@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_new_support_message_creates_ticket(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    log,
    db
):
    """Test the path to creating a zendesk ticket from new message receipt.
    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000001'
    group_id = '200000000002'

    # Set up the user details 'slack' will return    
    slack_client.users_info.return_value = FakeUserResponse()

    # No existing ticket should be returned:
    get_ticket.return_value = None

    # Return out fake ticket when asked to create:
    ticket = FakeTicket(ticket_id='32')
    create_ticket.return_value = ticket

    # There should be no entries here yet:
    assert ZenSlackChat.objects.count() == 0

    # Send a new help message
    payload = {
        'blocks': [{
            'block_id': 'Amzt',
            'elements': [{
                'elements': [{
                    'text': 'My 🖨 is on 🔥',
                    'type': 'text'
                }],
                'type': 'rich_text_section'
            }],
            'type': 'rich_text'
        }],
        'channel': 'C019JUGAGTS',
        'client_msg_id': '00676b39-4652-4a82-aa7a-7802355751cd',
        'event_ts': '1597940362.013100',
        'source_team': 'TGFJG8VEZ',
        'suppress_notification': False,
        'team': 'TGFJG8VEZ',
        'text': 'My 🖨 is on 🔥',
        'ts': '1597940362.013100',
        'user': 'UGF7MRWMS',
        'user_team': 'TGFJG8VEZ'
    }
    is_handled = handler(
        payload,
        our_channel='C019JUGAGTS',
        workspace_uri=workspace_uri,
        zendesk_uri=zendesk_uri,
        slack_client=slack_client,
        zendesk_client=zendesk_client,
        user_id=user_id,
        group_id=group_id,
    )
    assert is_handled is True

    # There should now be one instance here:
    assert ZenSlackChat.objects.count() == 1
    assert len(ZenSlackChat.open_issues()) == 1

    # Verify what the stored issue should look like:
    issue = ZenSlackChat.get('C019JUGAGTS', '1597940362.013100')
    assert issue.active is True
    assert issue.opened is not None
    assert issue.closed is None
    assert issue.channel_id == 'C019JUGAGTS'
    assert issue.chat_id == '1597940362.013100'
    assert issue.ticket_id == '32'

    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    slack_client.users_info.assert_called_with(user='UGF7MRWMS')

    # Check how zendesk api was called:
    create_ticket.assert_called_with(
        zendesk_client,
        chat_id='1597940362.013100',
        user_id='100000000001',
        group_id='200000000002',
        recipient_email='bob@example.com',
        subject='My 🖨 is on 🔥',
        slack_message_url='https://s.l.a.c.k/C019JUGAGTS/p1597940362013100'
    )

    # finally check the posted message:
    url = f'https://z.e.n.d.e.s.k/{ticket.id}'
    message = f"Hello, your new support request is {url}"
    post_message.assert_called_with(
        slack_client,
        '1597940362.013100',
        'C019JUGAGTS',
        message
    )


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
    

@patch('zenslackchat.message.add_comment')
@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
@pytest.mark.parametrize(
    'resolve_command',
    [
        'resolve ticket',
        'resolve',
        ':white_check_mark:',
        '✅',
        '🆗'
    ]
)
def test_zendesk_comment_and_resolve_ticket_command_closes_the_issue(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    add_comment,
    resolve_command, 
    log,
    db
):
    """Test a comment is sent to Zendesk and that a ticket can be resolved with
    the 'resolve ticket' message (not sent to Zendesk).

    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000004'
    group_id = '200000000005'

    slack_client.users_info.return_value = FakeUserResponse()
    get_ticket.return_value = None
    ticket = FakeTicket(ticket_id='77')
    create_ticket.return_value = ticket
    assert ZenSlackChat.objects.count() == 0

    def handle_message(payload):
        is_handled = handler(
            payload,
            our_channel='C0192NP3TFG',
            workspace_uri=workspace_uri,
            zendesk_uri=zendesk_uri,
            slack_client=slack_client,
            zendesk_client=zendesk_client,
            user_id=user_id,
            group_id=group_id,
        )
        assert is_handled is True

    # Create an issue
    #
    handle_message({
        'channel': 'C0192NP3TFG',
        'event_ts': '1602064330.001600',
        'text': 'My 🖨 is on 🔥',
        'ts': '1602064330.001600',
        'user': 'UGF7MRWMS',
    })

    # There should now be one instance here:
    assert ZenSlackChat.objects.count() == 1
    assert len(ZenSlackChat.open_issues()) == 1

    # Verify what the stored issue should look like:
    issue = ZenSlackChat.get('C0192NP3TFG', '1602064330.001600')
    assert issue.active is True
    assert issue.opened is not None
    assert issue.closed is None
    assert issue.channel_id == 'C0192NP3TFG'
    assert issue.chat_id == '1602064330.001600'
    assert issue.ticket_id == '77'

    # Check a new comment is sent over to zendesk:
    #
    create_ticket.reset_mock()
    post_message.reset_mock()

    # Return the fake ticket instance this time
    get_ticket.return_value = ticket

    handle_message({
        'channel': 'C0192NP3TFG',
        'event_ts': '1602064330.001600',
        'text': 'No wait, it was just a blinking red light',
        # This is a reply message so thread_ts refers to the parent chat id:
        'thread_ts': issue.chat_id,
        # and the ts refers to the reply message id:
        'ts': '1602065965.003200',
        'user': 'UGF7MRWMS',
    })
    assert ZenSlackChat.objects.count() == 1
    assert len(ZenSlackChat.open_issues()) == 1

    # None of test should have changed yet:
    issue = ZenSlackChat.get('C0192NP3TFG', '1602064330.001600')
    assert issue.active is True
    assert issue.opened is not None
    assert issue.closed is None
    assert issue.channel_id == 'C0192NP3TFG'
    assert issue.chat_id == '1602064330.001600'
    assert issue.ticket_id == '77'

    # No ticket should be created here
    create_ticket.assert_not_called()

    # Check the comment was "sent" to Zendesk correctly:
    add_comment.assert_called_with(
        zendesk_client,
        ticket,
        "Bob Sprocket (Slack): No wait, it was just a blinking red light"
    )

    # No slack message should have been sent:
    post_message.assert_not_called()

    # Resolve the issue:
    #
    create_ticket.reset_mock()
    post_message.reset_mock()
    add_comment.reset_mock()

    handle_message({
        'channel': 'C0192NP3TFG',
        'event_ts': '1602064330.001600',
        'text': resolve_command,
        # This is a reply message so thread_ts refers to the parent chat id
        'thread_ts': '1602064330.001600',
        'ts': '1602065965.003200',
        'user': 'UGF7MRWMS',
    })

    # There should now be one instance here:
    assert ZenSlackChat.objects.count() == 1
    assert len(ZenSlackChat.open_issues()) == 0

    # Verify what the stored issue should look like:
    issue = ZenSlackChat.get('C0192NP3TFG', '1602064330.001600')
    assert issue.active is False
    assert issue.opened is not None
    assert issue.closed is not None
    assert issue.channel_id == 'C0192NP3TFG'
    assert issue.chat_id == '1602064330.001600'
    assert issue.ticket_id == '77'

    slack_client.users_info.assert_called_with(user='UGF7MRWMS')
    create_ticket.assert_not_called()
    add_comment.assert_not_called()

    # Check the message that should go to slack closing the issue:
    url = f'https://z.e.n.d.e.s.k/{ticket.id}'
    post_message.assert_called_with(
        slack_client, 
        '1602064330.001600', 
        'C0192NP3TFG', 
        f'🤖 Understood. Ticket {url} has been closed.'
    )


@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_message_with_existing_support_ticket_in_zendesk(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    log,
    db
):
    """Test further in-thread messages don't result in new zendesk tickets.
    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000001'
    group_id = '200000000002'

    # Set up the user details 'slack' will return    
    slack_client.users_info.return_value = FakeUserResponse()

    # Return the ticket which will indicate we know about this issue and
    # not then go one to make a new message.
    ticket = FakeTicket(ticket_id='21')
    get_ticket.return_value = ticket

    # There should be no entries here yet:
    assert ZenSlackChat.objects.count() == 0

    # For this situation we need an exiting support ticket present for the 
    # message handler to detail with in our DB:
    ZenSlackChat.open(
        channel_id="C019JUGAGTS", 
        chat_id="1598022004.004900", 
        ticket_id="21", 
    )
    assert len(ZenSlackChat.open_issues()) == 1

    payload = {
        'blocks': [{
            'block_id': 'Amzt',
            'elements': [{
                'elements': [{
                    'text': 'Oh, wait, my bad 🤦‍♀️, its ok now.',
                    'type': 'text'
                }],
                'type': 'rich_text_section'
            }],
            'type': 'rich_text'
        }],
        'channel': 'C019JUGAGTS',
        'client_msg_id': '00676b39-4652-4a82-aa7a-7802355751cd',
        'event_ts': '1598022004.004900',
        'source_team': 'TGFJG8VEZ',
        'suppress_notification': False,
        'team': 'TGFJG8VEZ',
        'text': 'Oh, wait, my bad 🤦‍♀️, its ok now.',
        'ts': '1598022004.004900',
        'user': 'UGF7MRWMS',
        'user_team': 'TGFJG8VEZ'
    }
    is_handled = handler(
        payload,
        our_channel='C019JUGAGTS',
        workspace_uri=workspace_uri,
        zendesk_uri=zendesk_uri,
        slack_client=slack_client,
        zendesk_client=zendesk_client,
        user_id=user_id,
        group_id=group_id,
    )
    assert is_handled is True

    # There should not be any new issues as a result of this:
    results = ZenSlackChat.open_issues()
    assert len(results) == 1
    issue = results[0]
    assert issue.active is True
    assert issue.opened is not None
    assert issue.closed is None
    assert issue.channel_id == 'C019JUGAGTS'
    assert issue.chat_id == '1598022004.004900'
    assert issue.ticket_id == '21'
    
    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    slack_client.users_info.assert_called_with(user='UGF7MRWMS')

    # Quick check these should not have been called
    get_ticket.assert_not_called()
    create_ticket.assert_not_called()
    post_message.assert_not_called()


@patch('zenslackchat.message.add_comment')
@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_thread_message_with_support_ticket_in_zendesk(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    add_comment,
    log,
    db
):
    """Test in-thread conversation messages are shipped to Zendesk.
    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000001'
    group_id = '200000000002'

    # Set up the user details 'slack' will return    
    slack_client.users_info.return_value = FakeUserResponse()

    # Return the ticket which will indicate we know about this issue and
    # not then go one to make a new message.
    ticket = FakeTicket(ticket_id='83')
    get_ticket.return_value = ticket

    # There should be no entries here yet:
    assert ZenSlackChat.objects.count() == 0

    # For this situation we need an exiting support ticket present for the 
    # message handler to detail with in our DB:
    ZenSlackChat.open(
        channel_id="C019JUGAGTS", 
        chat_id="1598021907.003600", 
        ticket_id="83", 
    )
    assert len(ZenSlackChat.open_issues()) == 1

    # This is a message reply in the thread on slack:
    payload = {
        'blocks': [{
            'block_id': 'Amzt',
            'elements': [{
                'elements': [{
                    'text': 'Oh, wait, my bad 🤦‍♀️, its ok now.',
                    'type': 'text'
                }],
                'type': 'rich_text_section'
            }],
            'type': 'rich_text'
        }],
        'channel': 'C019JUGAGTS',
        'client_msg_id': '00676b39-4652-4a82-aa7a-7802355751cd',
        'event_ts': '1598022004.004900',
        'source_team': 'TGFJG8VEZ',
        'suppress_notification': False,
        'team': 'TGFJG8VEZ',
        'text': 'Oh, wait, my bad 🤦‍♀️, its ok now.',
        # ts & thread_ts set i.e. this is a message in a conversation and
        # thread_ts is the chat_id of the parent message.
        'thread_ts': '1598021907.003600',
        'ts': '1598022004.004900',
        'user': 'UGF7MRWMS',
        'user_team': 'TGFJG8VEZ'
    }
    is_handled = handler(
        payload,
        our_channel='C019JUGAGTS',
        workspace_uri=workspace_uri,
        zendesk_uri=zendesk_uri,
        slack_client=slack_client,
        zendesk_client=zendesk_client,
        user_id=user_id,
        group_id=group_id,
    )
    assert is_handled is True

    # There should be no new issues as a result of this:
    results = ZenSlackChat.open_issues()
    assert len(results) == 1
    issue = results[0]
    assert issue.active is True
    assert issue.opened is not None
    assert issue.closed is None
    assert issue.channel_id == 'C019JUGAGTS'
    assert issue.chat_id == '1598021907.003600'
    assert issue.ticket_id == '83'

    # Verify the calls to the various mock are as I expect. The only thing that
    # should happen here is the comment gets shipped to Zendesk

    # called with the content of data['user']
    slack_client.users_info.assert_called_with(user='UGF7MRWMS')

    # Check the ticket is "recovered" and the comment is "added" to it:
    get_ticket.assert_called_with(zendesk_client, '83')
    add_comment.assert_called_with(
        zendesk_client,
        ticket, 
        'Bob Sprocket (Slack): Oh, wait, my bad 🤦‍♀️, its ok now.'
    )

    # These should not have been called:
    create_ticket.assert_not_called()
    post_message.assert_not_called()


@patch('zenslackchat.message.add_comment')
@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_old_message_thread_with_message_and_no_support_ticket_in_zendesk(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    add_comment,
    log,
    db
):
    """Test when old message threads are replied to.

    When no ticket is found in zendesk and ts & thread_ts are set, This
    indicates an old message thread with new chatter on it. I'm going to ignore 
    this. We just log that we ignore it and move on.

    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000001'
    group_id = '200000000002'

    # Set up the user details 'slack' will return    
    slack_client.users_info.return_value = FakeUserResponse()

    # With no known issue for this and set ts & thread_ts, it will indicate an 
    # old message thread with new chatter on it. I'm going to ignore this.
    get_ticket.return_value = None
    assert len(ZenSlackChat.open_issues()) == 0

    # Send a new help message
    payload = {
        'blocks': [{
            'block_id': 'Amzt',
            'elements': [{
                'elements': [{
                    'text': 'What 🕙 is it?',
                    'type': 'text'
                }],
                'type': 'rich_text_section'
            }],
            'type': 'rich_text'
        }],
        'channel': 'C019JUGAGTS',
        'client_msg_id': '00676b39-4652-4a82-aa7a-7802355751cd',
        'event_ts': '1598021977.004100',
        'source_team': 'TGFJG8VEZ',
        'suppress_notification': False,
        'team': 'TGFJG8VEZ',
        'text': 'What 🕙 is it?',
        # ts & thread_ts set
        'thread_ts': '1598021907.003600',
        'ts': '1598021977.004100',
        'user': 'UGF7MRWMS',
        'user_team': 'TGFJG8VEZ'
    }
    is_handled = handler(
        payload,
        our_channel='C019JUGAGTS',
        workspace_uri=workspace_uri,
        zendesk_uri=zendesk_uri,
        slack_client=slack_client,
        zendesk_client=zendesk_client,
        user_id=user_id,
        group_id=group_id,
    )
    assert is_handled is True

    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    slack_client.users_info.assert_called_with(user='UGF7MRWMS')

    # In a conversation the thread_ts is actually a reference to the parent 
    # message and ts refers to the message that has come in. Check this has 
    # been taken into account.

    # No new issue should be created in this case
    assert len(ZenSlackChat.open_issues()) == 0

    # These won't be called as we don't have a record of this conversation:
    add_comment.assert_not_called()
    get_ticket.assert_not_called()
    create_ticket.assert_not_called()
    post_message.assert_not_called()


@pytest.mark.parametrize(
    'ignored_subtype',
    IGNORED_SUBTYPES
)
@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_message_events_that_are_ignored_by_handler(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    ignored_subtype,
    log,
    db
):
    """Verify that I don't handle various subtype messages.
    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000001'
    group_id = '200000000002'
    slack_client.users_info.return_value = {}
    payload = {
        'channel': 'C019JUGAGTS',
        'subtype': ignored_subtype,
        'ts': '1597937653.011100'
    }
    is_handled = handler(
        payload,
        our_channel='C019JUGAGTS',
        workspace_uri=workspace_uri,
        zendesk_uri=zendesk_uri,
        slack_client=slack_client,
        zendesk_client=zendesk_client,
        user_id=user_id,
        group_id=group_id,
    )
    assert is_handled is False
    slack_client.users_info.assert_not_called()


@patch('zenslackchat.message.add_comment')
@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_channel_is_not_our_channel_so_message_is_ignored(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    add_comment,
    log,
    db
):
    """Verify that I don't handle events not from our channel.
    """
    slack_client = MagicMock()
    zendesk_client = MagicMock()
    workspace_uri = 'https://s.l.a.c.k'
    zendesk_uri = 'https://z.e.n.d.e.s.k'
    user_id = '100000000001'
    group_id = '200000000002'
    slack_client.users_info.return_value = {}
    payload = {
        'channel': 'C01A96HA9BR',
        'event_ts': '1598021977.004100',
        'source_team': 'TGFJG8VEZ',
        'text': 'blah blah blah',
        'ts': '1598021977.004100',
        'user': 'UGF7MRWMS',
    }
    is_handled = handler(
        payload,
        our_channel='C019JUGAGTS',
        workspace_uri=workspace_uri,
        zendesk_uri=zendesk_uri,
        slack_client=slack_client,
        zendesk_client=zendesk_client,
        user_id=user_id,
        group_id=group_id,
    )
    assert is_handled is False
    slack_client.users_info.assert_not_called()
    add_comment.assert_not_called()
    get_ticket.assert_not_called()
    create_ticket.assert_not_called()
    post_message.assert_not_called()

