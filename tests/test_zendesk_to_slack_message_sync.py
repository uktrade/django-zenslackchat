from datetime import datetime
from datetime import timezone

from zenslackchat.message import messages_for_slack

UTC = timezone.utc


def test_message_for_slack_1(log):
    """Capture behaviour whereby zendesk messages are getting readded to slack.
    """
    zendesk = [
        {'attachments': [],
        'audit_id': 683599479617,
        'author_id': 375202855898,
        'body': 'Oisin Mulvihill (Slack): nice dog',
        'created_at': datetime(2020, 9, 9, 16, 12, 27, tzinfo=timezone.utc),
        'id': 683599479657,
        'public': True,
        'type': 'Comment',
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'attachments': [],
        'audit_id': 683726086418,
        'author_id': 375202855898,
        'body': '(Zendesk): :dog:',
        'created_at': datetime(2020, 9, 9, 16, 11, 36, tzinfo=timezone.utc),
        'id': 683726086538,
        'public': True,
        'type': 'Comment',
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'attachments': [],
        'audit_id': 683598728197,
        'author_id': 375202855898,
        'body': 'Oisin Mulvihill (Slack): hello',
        'created_at': datetime(2020, 9, 9, 16, 10, 49, tzinfo=timezone.utc),
        'id': 683598728297,
        'public': True,
        'type': 'Comment',
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'attachments': [],
        'audit_id': 683598561597,
        'author_id': 375202855898,
        'body': 'This is the message on slack <link>.',
        'created_at': datetime(2020, 9, 9, 16, 10, 29, tzinfo=timezone.utc),
        'id': 683598561657,
        'public': True,
        'type': 'Comment',
        'via': {'channel': 'api',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}},
        {'attachments': [],
        'audit_id': 683623144457,
        'author_id': 375202855898,
        'body': '♻\u200b',
        'created_at': datetime(2020, 9, 9, 17, 8, 14, tzinfo=timezone.utc),
        'id': 683623144537,
        'public': True,
        'type': 'Comment',
        'via': {'channel': 'web',
                'source': {'from': {}, 'from_': None, 'rel': None, 'to': {}}}}                
    ]

    slack = [
        {'client_msg_id': '32a8b910-7a98-4df4-8011-293bbbccd96f',
        'created_at': datetime(2020, 9, 9, 16, 10, 26, tzinfo=timezone.utc),
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
        'parent_user_id': 'UGF7MRWMS',
        'team': 'TGFJG8VEZ',
        'text': 'Hello, your new support request is <link>',
        'thread_ts': '1599667826.017500',
        'ts': '1599667829.017600',
        'type': 'message',
        'user': 'U01AKS3HDJ5'},
        {'client_msg_id': 'b18e3f6f-ce82-4fa9-a1a7-1b67d06a0a4f',
        'created_at': datetime(2020, 9, 9, 16, 10, 47, tzinfo=timezone.utc),
        'parent_user_id': 'UGF7MRWMS',
        'team': 'TGFJG8VEZ',
        'text': 'hello',
        'thread_ts': '1599667826.017500',
        'ts': '1599667847.017800',
        'type': 'message',
        'user': 'UGF7MRWMS'},
        {'bot_id': 'B01ADD673UL',
        'created_at': datetime(2020, 9, 9, 16, 11, 42, tzinfo=timezone.utc),
        'parent_user_id': 'UGF7MRWMS',
        'team': 'TGFJG8VEZ',
        'text': '(Zendesk): :dog:',
        'thread_ts': '1599667826.017500',
        'ts': '1599667902.018000',
        'type': 'message',
        'user': 'U01AKS3HDJ5'},
        {'client_msg_id': 'd38ad064-968d-4177-8364-e82a56082ddc',
        'created_at': datetime(2020, 9, 9, 16, 12, 24, tzinfo=timezone.utc),
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
    

