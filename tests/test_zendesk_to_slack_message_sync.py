from datetime import datetime
from datetime import timezone

from zenslackchat.message import messages_for_slack

UTC = timezone.utc


def test_emoji_bug(log):
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
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=timezone.utc),
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'body': '👍',
        'created_at': datetime(2020, 9, 9, 17, 8, 14, tzinfo=timezone.utc),
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
    ]

    slack = [
        {'created_at': datetime(2020, 9, 9, 16, 10, 26, tzinfo=timezone.utc),
        'text': ':fish:',
        'thread_ts': '1599667826.017500',
        'ts': '1599667826.017500',
        'type': 'message',
        'user': 'UGF7MRWMS'},
        {'bot_id': 'B01ADD673UL',
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=timezone.utc),
        'text': 'Hello, your new support request is <link>',
        'thread_ts': '1599667826.017500',
        'ts': '1599667829.017600',
        'type': 'message',
        'user': 'U01AKS3HDJ5'},
        {'bot_id': 'B01ADD673UL',
        'created_at': datetime(2020, 9, 9, 16, 11, 42, tzinfo=timezone.utc),
        'text': '(Zendesk): :thumbs_up:',
        'thread_ts': '1599667826.017500',
        'ts': '1599667902.018000',
        'type': 'message',
        'user': 'U01AKS3HDJ5'},
    ]    

    results = messages_for_slack(slack, zendesk)

    # The 👍 is already present on slack as the mesasge '(Zendesk): :thumb:'. 
    # Check there are no new messages as a result.

    # There should be 
    assert len(results) == 0
    

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
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=timezone.utc),
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'body': '👍',
        'created_at': datetime(2020, 9, 9, 17, 8, 14, tzinfo=timezone.utc),
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
    ]

    slack = [
        {'created_at': datetime(2020, 9, 9, 16, 10, 26, tzinfo=timezone.utc),
        'text': ':fish:',
        'thread_ts': '1599667826.017500',
        'ts': '1599667826.017500',
        'type': 'message',
        'user': 'UGF7MRWMS'},
        {'bot_id': 'B01ADD673UL',
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=timezone.utc),
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
