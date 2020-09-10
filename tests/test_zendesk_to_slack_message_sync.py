from datetime import datetime
from datetime import timezone

from zenslackchat.message import messages_for_slack

UTC = timezone.utc


def test_emoji_bug(log):
    """
    """
    # The fixture data is not complete just the fields I'm using to recreate
    # the bug
    zendesk = [
        {
        'author_id': 375202855898,
        'body': 'Oisin Mulvihill (Slack): nice dog',
        'created_at': datetime(2020, 9, 9, 16, 12, 27, tzinfo=timezone.utc),
        'id': 683599479657,
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'author_id': 375202855898,
        'body': '(Zendesk): :dog:',
        'created_at': datetime(2020, 9, 9, 16, 11, 36, tzinfo=timezone.utc),
        'id': 683726086538,
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'author_id': 375202855898,
        'body': 'Oisin Mulvihill (Slack): hello',
        'created_at': datetime(2020, 9, 9, 16, 10, 49, tzinfo=timezone.utc),
        'id': 683598728297,
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'author_id': 375202855898,
        'body': 'This is the message on slack <link>.',
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=timezone.utc),
        'id': 683598561657,
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'author_id': 375202855898,
        'body': '♻\u200b',
        'created_at': datetime(2020, 9, 9, 17, 8, 14, tzinfo=timezone.utc),
        'id': 683623144537,
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}}                
    ]

    slack = [
        {'created_at': datetime(2020, 9, 9, 16, 10, 26, tzinfo=timezone.utc),
        'latest_reply': '1599667944.018200',
        'reply_count': 4,
        'reply_users': ['U01AKS3HDJ5', 'UGF7MRWMS'],
        'reply_users_count': 2,
        'subscribed': False,
        'team': 'TGFJG8VEZ',
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
        {'created_at': datetime(2020, 9, 9, 16, 10, 47, tzinfo=timezone.utc),
        'text': 'hello',
        'thread_ts': '1599667826.017500',
        'ts': '1599667847.017800',
        'type': 'message',
        'user': 'UGF7MRWMS'},
        {'bot_id': 'B01ADD673UL',
        'created_at': datetime(2020, 9, 9, 16, 11, 42, tzinfo=timezone.utc),
        'text': '(Zendesk): :dog:',
        'thread_ts': '1599667826.017500',
        'ts': '1599667902.018000',
        'type': 'message',
        'user': 'U01AKS3HDJ5'},
        {'created_at': datetime(2020, 9, 9, 16, 12, 24, tzinfo=timezone.utc),
        'parent_user_id': 'UGF7MRWMS',
        'team': 'TGFJG8VEZ',
        'text': 'nice dog',
        'thread_ts': '1599667826.017500',
        'ts': '1599667944.018200',
        'type': 'message',
        'user': 'UGF7MRWMS'}
    ]    

    results = messages_for_slack(slack, zendesk)

    # There should be 
    assert len(results) == 0
    

