from unittest.mock import patch
from unittest.mock import MagicMock

from zenslackchat.message import handler



@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_new_message_creates_ticket(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket
):
    """Test deleted or changed messages are rejected.
    """
    mock_web_client = MagicMock()
    mock_web_client.users_info.return_value = {}

    # modified copy-n-pasted message event
    payload = {
        'data': {
            'blocks': [{
                'block_id': 'Amzt',
                'elements': [{
                    'elements': [{
                        'text': 'new message',
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
            'text': 'new message',
            'ts': '1597940362.013100',
            'user': 'UGF7MRWMS',
            'user_team': 'TGFJG8VEZ'
        },
        'rtm_client': 'rtm_client',
        'web_client': mock_web_client
    }

    is_handled = handler(payload)
    assert is_handled is True
    mock_web_client.users_info.assert_not_called()





@patch('zenslackchat.message.get_ticket')
@patch('zenslackchat.message.close_ticket')
@patch('zenslackchat.message.create_ticket')
@patch('zenslackchat.message.post_message')
def test_message_events_that_are_ignored_by_handler(
    post_message,
    create_ticket,
    close_ticket,
    get_ticket
):
    """Test deleted or changed messages are rejected.
    """
    mock_web_client = MagicMock()
    mock_web_client.users_info.return_value = {}

    # a copy-n-pasted message_change event without blocks as they're too long.
    payload = {
        'data': {
            'channel': 'C019JUGAGTS',
            'event_ts': '1597937653.011100',
            'hidden': True,
            'message': {
                'blocks': [],
                'client_msg_id': '7f3a9e3f-2873-4aa4-a364-b11f636e876f',
                'latest_reply': '1597935682.010800',
                'reply_count': 14,
                'reply_users': ['B0197PEUFDF', 'UGF7MRWMS'],
                'reply_users_count': 2,
                'team': 'TGFJG8VEZ',
                'text': 'help my printer is on :fire:',
                'thread_ts': '1597931771.007500',
                'ts': '1597931771.007500',
                'type': 'message',
                'user': 'UGF7MRWMS'
            },
            'previous_message': {
                'blocks': [],
                'client_msg_id': '7f3a9e3f-2873-4aa4-a364-b11f636e876f',
                'last_read': '1597935682.010800',
                'latest_reply': '1597935682.010800',
                'reply_count': 14,
                'reply_users': ['B0197PEUFDF', 'UGF7MRWMS'],
                'reply_users_count': 2,
                'subscribed': True,
                'team': 'TGFJG8VEZ',
                'text': 'help my printer is on :fire:',
                'thread_ts': '1597931771.007500',
                'ts': '1597931771.007500',
                'type': 'message',
                'user': 'UGF7MRWMS'
            },
            'subtype': 'message_changed',
            'ts': '1597937653.011100'
        },
        'rtm_client': 'rtm_client',
        'web_client': mock_web_client
    }
    is_handled = handler(payload)
    assert is_handled is False
    mock_web_client.users_info.assert_not_called()

    # a copy-n-pasted message_deleted event without blocks as they're too long.
    payload = {
        'data': {
            'channel': 'C019JUGAGTS',
            'deleted_ts': '1597935076.009400',
            'event_ts': '1597937653.011000',
            'hidden': True,
            'previous_message': {
                'blocks': [],
                'client_msg_id': '69c16757-d27a-4cd9-b855-062e7025fc0e',
                'parent_user_id': 'UGF7MRWMS',
                'team': 'TGFJG8VEZ',
                'text': 'also no',
                'thread_ts': '1597931771.007500',
                'ts': '1597935076.009400',
                'type': 'message',
                'user': 'UGF7MRWMS'
            },
            'subtype': 'message_deleted',
            'ts': '1597937653.011000'
        },
        'rtm_client': 'rtm_client',
        'web_client': mock_web_client
    }    
    is_handled = handler(payload)
    assert is_handled is False
    mock_web_client.users_info.assert_not_called()

    # Bot message without icons as they're too long:
    payload = {
        'data': {
            'bot_id': 'B0197PEUFDF',
            'bot_profile': {
                'app_id': 'A0F7YS25R',
                'deleted': False,
                'icons': {},
                'id': 'B0197PEUFDF',
                'name': 'bot',
                'team_id': 'TGFJG8VEZ',
                'updated': 1597399574
            },
            'channel': 'C019JUGAGTS',
            'event_ts': '1597935682.010800',
            'source_team': 'TGFJG8VEZ',
            'subtype': 'bot_message',
            'suppress_notification': False,
            'team': 'TGFJG8VEZ',
            'text': ':robot_face: Understood.',
            'thread_ts': '1597931771.007500',
            'ts': '1597935682.010800',
            'user_team': 'TGFJG8VEZ',
            'username': 'bot'
        },
        'rtm_client': 'rtm_client',
        'web_client': mock_web_client
    }
    is_handled = handler(payload)
    assert is_handled is False
    mock_web_client.users_info.assert_not_called()

    # a copy-n-pasted message_replied event without blocks as they're too long.
    payload = {
        'data': {
            'channel': 'C019JUGAGTS',
            'event_ts': '1597938085.011300',
            'hidden': True,
            'message': {
                'blocks': [],
                'client_msg_id': '7f3a9e3f-2873-4aa4-a364-b11f636e876f',
                'latest_reply': '1597938085.011200',
                'reply_count': 15,
                'reply_users': ['B0197PEUFDF', 'UGF7MRWMS'],
                'reply_users_count': 2,
                'team': 'TGFJG8VEZ',
                'text': 'help my printer is on :fire:',
                'thread_ts': '1597931771.007500',
                'ts': '1597931771.007500',
                'type': 'message',
                'user': 'UGF7MRWMS'
            },
            'subtype': 'message_replied',
            'ts': '1597938085.011300'
        },
        'rtm_client': 'rtm_client',
        'web_client': mock_web_client
    }
    is_handled = handler(payload)
    assert is_handled is False
    mock_web_client.users_info.assert_not_called()
