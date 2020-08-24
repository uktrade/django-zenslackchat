from unittest.mock import patch
from unittest.mock import MagicMock

import pytest

from zenslackchat import slack_utils
from zenslackchat.message import handler



class FakeTicket(object):
    def __init__(self, ticket_id):
        self.id = ticket_id


class FakeUserResponse(object):
    def __init__(self):
        self.data = dict(
            user=dict(
                profile=dict(
                    email='bob@example.com'
                )
            )
        )


@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_new_support_message_creates_ticket(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    log
):
    """Test the path to creating a zendesk ticket from new message receipt.
    """
    mock_rtm_client = MagicMock()
    mock_web_client = MagicMock()

    # Set up the user details 'slack' will return    
    mock_web_client.users_info.return_value = FakeUserResponse()

    # No existing ticket should be returned:
    get_ticket.return_value = None

    # Return out fake ticket when asked to create:
    ticket = FakeTicket(ticket_id='32')
    create_ticket.return_value = ticket

    # Send a new help message
    payload = {
        'data': {
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
        },
        'rtm_client': mock_rtm_client,
        'web_client': mock_web_client
    }
    env = {
        'SLACK_WORKSPACE_URI': 'https://example.com/',
        'ZENDESK_TICKET_URI': 'https://example.com/agent/tickets/'
    }
    with patch.dict('os.environ', env, clear=True):    
        is_handled = handler(payload)
    assert is_handled is True

    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    mock_web_client.users_info.assert_called_with(user='UGF7MRWMS')

    # called with the content of data['ts'] which in this test resulted in
    # None being returned (no ticket found).
    get_ticket.assert_called_with('1597940362.013100')

    # Check how zendesk api was called:
    create_ticket.assert_called_with(
        chat_id='1597940362.013100',
        recipient_email='bob@example.com',
        subject='My 🖨 is on 🔥',
        slack_message_url='https://example.com/C019JUGAGTS/p1597940362013100'
    )

    # finally check the posted message:
    url = f'https://example.com/agent/tickets/{ticket.id}'
    message = f"Hello, your new support request is {url}"
    post_message.assert_called_with(
        mock_web_client,
        '1597940362.013100',
        'C019JUGAGTS',
        message
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
    log
):
    """Test further in-thread messages don't result in new zendesk tickets.
    """
    mock_rtm_client = MagicMock()
    mock_web_client = MagicMock()

    # Set up the user details 'slack' will return    
    mock_web_client.users_info.return_value = FakeUserResponse()

    # Return the ticket which will indicate we know about this issue and
    # not then go one to make a new message.
    ticket = FakeTicket(ticket_id='32')
    get_ticket.return_value = ticket

    payload = {
        'data': {
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
        },
        'rtm_client': mock_rtm_client,
        'web_client': mock_web_client
    }
    env = {
        'SLACK_WORKSPACE_URI': 'https://example.com/',
        'ZENDESK_TICKET_URI': 'https://example.com/agent/tickets/'
    }
    with patch.dict('os.environ', env, clear=True):    
        is_handled = handler(payload)
    assert is_handled is True

    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    mock_web_client.users_info.assert_called_with(user='UGF7MRWMS')

    # called with the content of data['ts'] which in this test resulted in
    # None being returned (no ticket found).
    get_ticket.assert_called_with('1598022004.004900')

    # Check how zendesk api was called:
    create_ticket.assert_not_called()

    # finally check the posted message:
    post_message.assert_not_called()


@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_thread_message_with_support_ticket_in_zendesk(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    log
):
    """Test in-thread messages is shipped to Zendesk.
    """
    mock_rtm_client = MagicMock()
    mock_web_client = MagicMock()

    # Set up the user details 'slack' will return    
    mock_web_client.users_info.return_value = FakeUserResponse()

    # Return the ticket which will indicate we know about this issue and
    # not then go one to make a new message.
    ticket = FakeTicket(ticket_id='32')
    get_ticket.return_value = ticket

    # This is a message reply in the thread on slack:
    payload = {
        'data': {
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
            # ts & thread_ts set
            'thread_ts': '1598021907.003600',
            'ts': '1598022004.004900',
            'user': 'UGF7MRWMS',
            'user_team': 'TGFJG8VEZ'
        },
        'rtm_client': mock_rtm_client,
        'web_client': mock_web_client
    }
    env = {
        'SLACK_WORKSPACE_URI': 'https://example.com/',
        'ZENDESK_TICKET_URI': 'https://example.com/agent/tickets/'
    }
    with patch.dict('os.environ', env, clear=True):    
        is_handled = handler(payload)
    assert is_handled is True

    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    mock_web_client.users_info.assert_called_with(user='UGF7MRWMS')

    # In this case the thread_ts is the parent chat id we use:
    get_ticket.assert_called_with('1598021907.003600')

    # Check how zendesk api was called:
    create_ticket.assert_not_called()

    # finally check the posted message:
    post_message.assert_not_called()


@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_old_message_thread_with_message_and_no_support_ticket_in_zendesk(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket,
    log
):
    """Test when old message threads are replied to.

    When no ticket is found in zendesk and ts & thread_ts are set, This
    indicates an old message thread with new chatter on it. I'm going to ignore 
    this. We just log that we ignore it and move on.

    """
    mock_rtm_client = MagicMock()
    mock_web_client = MagicMock()

    # Set up the user details 'slack' will return    
    mock_web_client.users_info.return_value = FakeUserResponse()

    # Return no ticket and set ts & thread_ts. This will indicate an old 
    # message thread with new chatter on it. I'm going to ignore this.
    get_ticket.return_value = None

    # Send a new help message
    payload = {
        'data': {
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
        },
        'rtm_client': mock_rtm_client,
        'web_client': mock_web_client
    }
    env = {
        'SLACK_WORKSPACE_URI': 'https://example.com/',
        'ZENDESK_TICKET_URI': 'https://example.com/agent/tickets/'
    }
    with patch.dict('os.environ', env, clear=True):    
        is_handled = handler(payload)
    assert is_handled is True

    # Verify the calls to the various mock are as I expect:

    # called with the content of data['user']
    mock_web_client.users_info.assert_called_with(user='UGF7MRWMS')

    # In a conversation the thread_ts is actually a reference to the parent 
    # message and ts refers to the message that has come in. Check this has 
    # been taken into account:
    get_ticket.assert_called_with('1598021907.003600')

    # Check how zendesk api was called:
    create_ticket.assert_not_called()

    # finally check the posted message:
    post_message.assert_not_called()


@pytest.mark.parametrize(
    'ignored_subtype',
    [
        'channel_join', 'bot_message', 'channel_rename', 'message_changed', 
        'message_deleted',
    ]
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
    log
):
    """Verify that I don't handle various subtype messages.
    """
    mock_web_client = MagicMock()
    mock_web_client.users_info.return_value = {}
    payload = {
        'data': {
            'channel': 'C019JUGAGTS',
            'subtype': ignored_subtype,
            'ts': '1597937653.011100'
        },
        'rtm_client': 'rtm_client',
        'web_client': mock_web_client
    }
    is_handled = handler(payload)
    assert is_handled is False
    mock_web_client.users_info.assert_not_called()
