from unittest.mock import patch
from unittest.mock import MagicMock

import pytest

from zenslackchat.message_tools import messages_for_slack


def test_email_created_issue_bug(log):
    """Walk through the message comparrison for email created issue.
    """
    # for no inputs we should get no outputs:
    assert messages_for_slack([], []) == []

    slack_messages = [
        {
            "bot_id": "B01ADD673UL",
            "type": "message",
            "text": "(From Zendesk Email): subject 789",
            "user": "U01AKS3HDJ5",
            "ts": "1608143093.004600",
            "team": "TGFJG8VEZ",
            "bot_profile": {
                "id": "B01ADD673UL",
                "deleted": False,
                "name": "ZenSlackChat",
                "updated": 1599473694,
                "app_id": "A01A748235G",
                "icons": {
                    "image_36": "https://a.slack-edge.com/.../bot_36.png",
                    "image_48": "https://a.slack-edge.com/.../bot_48.png",
                    "image_72": "https://a.slack-edge.com/.../service_72.png"
                },
                "team_id": "TGFJG8VEZ"
            },
            "thread_ts": "1608143093.004600",
            "reply_count": 4,
            "reply_users_count": 2,
            "latest_reply": "1608226536.010400",
            "reply_users": [
                "U01AKS3HDJ5",
                "UGF7MRWMS"
            ],
            "subscribed": False
        },
        {
            "bot_id": "B01ADD673UL",
            "type": "message",
            "text": "Hello, your new support request is <https://.../33680>",
            "user": "U01AKS3HDJ5",
            "ts": "1608143094.004700",
            "team": "TGFJG8VEZ",
            "bot_profile": {
                "id": "B01ADD673UL",
                "deleted": False,
                "name": "ZenSlackChat",
                "updated": 1599473694,
                "app_id": "A01A748235G",
                "icons": {
                    "image_36": "https://a.slack-edge.com/.../bot_36.png",
                    "image_48": "https://a.slack-edge.com/.../bot_48.png",
                    "image_72": "https://a.slack-edge.com/.../service_72.png"
                },
                "team_id": "TGFJG8VEZ"
            },
            "thread_ts": "1608143093.004600",
            "parent_user_id": "U01AKS3HDJ5"
        },
        {
            "bot_id": "B01ADD673UL",
            "type": "message",
            "text": "(Zendesk): email body of 789\n\n\n\n",
            "user": "U01AKS3HDJ5",
            "ts": "1608143095.004900",
            "team": "TGFJG8VEZ",
            "bot_profile": {
                "id": "B01ADD673UL",
                "deleted": False,
                "name": "ZenSlackChat",
                "updated": 1599473694,
                "app_id": "A01A748235G",
                "icons": {
                    "image_36": "https://a.slack-edge.com/.../bot_36.png",
                    "image_48": "https://a.slack-edge.com/.../bot_48.png",
                    "image_72": "https://a.slack-edge.com/.../service_72.png"
                },
                "team_id": "TGFJG8VEZ"
            },
            "thread_ts": "1608143093.004600",
            "parent_user_id": "U01AKS3HDJ5"
        }
    ]

    zendesk_messages =[
        {
            "attachments": [],
            "author_id": 375202855898,
            "body": (
                "email body of 789\n\n\n\n--\n\n\n\nOisin Mulvihill | Webops/SRE |"
                " Digital\n\nDepartment for International Trade | 50 Victoria Stre"
                "et, London SW1E 5LB | E-mail: oisin.mulvihill@...\n\n\n\n\nCommun"
                "ications with the Department for International Trade may be autom"
                "atically logged, monitored and/or recorded for legal purposes."
            ),
            "created_at": "2020-12-16T18:24:51Z",
            "id": 737023086398,
            "public": True,
            "type": "Comment",
            "html_body": "...",
            "plain_body": (
                "email body of 789\n\n\n\n--\n\n\n\nOisin Mulvihill | Webops/SRE |"
                " Digital\n\nDepartment for International Trade | 50 Victoria Stre"
                "et, London SW1E 5LB | E-mail: oisin.mulvihill@...\n\n\n\n\nCommun"
                "ications with the Department for International Trade may be autom"
                "atically logged, monitored and/or recorded for legal purposes."
            ),
            "audit_id": 737023086318,
            "metadata": {
                "custom": {},
                "suspension_type_id": None,
                "system": {
                    "client": None,
                    "ip_address": None,
                    "latitude": 52.0,
                    "location": "ENG, United Kingdom",
                    "longitude": 0.0,
                    "message_id": "...",
                    "raw_email_identifier": "...eml",
                    "json_email_identifier": "...json"
                }
            },
            "via": {
                "channel": "email",
                "source": {
                    "from_": None,
                    "rel": None,
                    "to": {
                        "name": "Department for International Trade",
                        "address": "...zendesk.com"
                    },
                    "from": {
                        "address": "oisin.mulvihill@...",
                        "name": "zenslackchat",
                        "original_recipients": [
                            "oisin.mulvihill@...",
                            "...zendesk.com"
                        ]
                    }
                }
            }
        },
        {
            "attachments": [],
            "author_id": 375202855898,
            "body": (
                "The SRE team is aware of your issue on Slack here https://..."
            ),
            "created_at": "2020-12-16T18:24:54Z",
            "id": 737023107998,
            "public": True,
            "type": "Comment",
            "html_body": "...",
            "plain_body": (
                "The SRE team is aware of your issue on Slack here https://..."
            ),
            "audit_id": 737023107958,
            "metadata": {
                "custom": {},
                "system": {
                    "client": "Zenpy/2.0.10",
                    "ip_address": "1.2.3.4",
                    "latitude": 52.0,
                    "location": "ENG, United Kingdom",
                    "longitude": 0.0
                }
            },
            "via": {
                "channel": "api",
                "source": {
                    "from_": None,
                    "rel": None,
                    "to": {},
                    "from": {}
                }
            }
        },
    ]

    # There should no difference in this case either
    assert messages_for_slack(slack_messages, zendesk_messages) == []


def test_normal_issue_flow(log):
    """Walk through the message comparrison for slack created issue.
    """
    # for no inputs we should get no outputs:
    assert messages_for_slack([], []) == []

    slack_issue = [
        {
            "client_msg_id": "aa8a191e-0391-4ade-8f6a-84da6200313b",
            "type": "message",
            "text": "new issue",
            "user": "UGF7MRWMS",
            "ts": "1608291472.001600",
            "team": "TGFJG8VEZ",
            "blocks": [
                {
                    "type": "rich_text",
                    "block_id": "1LmQ",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": "new issue"
                                }
                            ]
                        }
                    ]
                }
            ],
            "thread_ts": "1608291472.001600",
            "reply_count": 1,
            "reply_users_count": 1,
            "latest_reply": "1608291475.001700",
            "reply_users": [
                "U01AKS3HDJ5"
            ],
            "subscribed": False
        },
        {
            "bot_id": "B01ADD673UL",
            "type": "message",
            "text": "Hello, your new support request is <https://staging-uktrade.zendesk.com/agent/tickets/33686>",
            "user": "U01AKS3HDJ5",
            "ts": "1608291475.001700",
            "team": "TGFJG8VEZ",
            "bot_profile": {
                "id": "B01ADD673UL",
                "deleted": False,
                "name": "ZenSlackChat",
                "updated": 1599473694,
                "app_id": "A01A748235G",
                "icons": {
                    "image_36": "https://a.slack-edge../bot_36.png",
                    "image_48": "https://a.slack-edge../bot_48.png",
                    "image_72": "https://a.slack-edge../service_72.png"
                },
                "team_id": "TGFJG8VEZ"
            },
            "thread_ts": "1608291472.001600",
            "parent_user_id": "UGF7MRWMS"
        }
    ]

    zendesk_with_link_to_slack = {
        "attachments": [],
        "author_id": 375202855898,
        "body": "This is the message on slack https://falconspacebasecamp.slack.com/archives/C0192NP3TFG/p1608291472001600.",
        "created_at": "2020-12-18T11:37:54Z",
        "id": 738390162017,
        "public": True,
        "type": "Comment",
        "html_body": "<div class=\"zd-comment\" dir=\"auto\"><p dir=\"auto\">This is the message on slack <a href=\"https://falconspacebasecamp.slack.com/archives/C0192NP3TFG/p1608291472001600\" rel=\"noreferrer\">https://falconspacebasecamp.slack.com/archives/C0192NP3TFG/p1608291472001600</a>.</p></div>",
        "plain_body": "This is the message on slack https://falconspacebasecamp.slack.com/archives/C0192NP3TFG/p1608291472001600.",
        "audit_id": 738390161937,
        "metadata": {
            "custom": {},
            "system": {
                "client": "Zenpy/2.0.10",
                "ip_address": "1.2.3.4",
                "latitude": 52.0,
                "location": "ENG, United Kingdom",
                "longitude": 0.0
            }
        },
        "via": {
            "channel": "api",
            "source": {
                "from_": None,
                "rel": None,
                "to": {},
                "from": {}
            }
        }
    }

    # When an issue is create via slack, zenslackchat also adds a comment on
    # zendesk linking back to this issue on slack. If I compare slack/zendesk
    # now I should no new message for slack
    #
    assert messages_for_slack(
        slack_issue, [zendesk_with_link_to_slack]
    ) == []


    # Now a comment is made on Zendesk. Check this results in a message for 
    # slack.
    #
    first_comment_from_zendesk = {
        "attachments": [],
        "author_id": 10361731669,
        "body": "first comment from zendesk",
        "created_at": "2020-12-18T11:41:05Z",
        "id": 738392387837,
        "public": True,
        "type": "Comment",
        "html_body": "<..>",
        "plain_body": "first comment from zendesk",
        "audit_id": 738392387737,
        "metadata": {
            "custom": {},
            "system": {
                "client": "Mozilla/5.0 ...",
                "ip_address": "1.2.3.4",
                "latitude": 52.0,
                "location": "ENG, United Kingdom",
                "longitude": 0.0
            }
        },
        "via": {
            "channel": "web",
            "source": {
                "from_": None,
                "rel": None,
                "to": {},
                "from": {}
            }
        }
    }
    assert messages_for_slack(
        slack_issue, 
        [zendesk_with_link_to_slack, first_comment_from_zendesk]
    ) == [
        first_comment_from_zendesk
    ]

    # Now a message is create on slack, this is synced with zendesk. Check this
    # does not result in a message for slack.
    #
    first_slack_comment = {
        "client_msg_id": "fb27b8e3-abdd-4484-a93b-1c816568b025",
        "type": "message",
        "text": "first comment from slack",
        "user": "UGF7MRWMS",
        "ts": "1608291879.002100",
        "team": "TGFJG8VEZ",
        "blocks": [
            {
                "type": "rich_text",
                "block_id": "AD5SC",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": "first comment from slack"
                            }
                        ]
                    }
                ]
            }
        ],
        "thread_ts": "1608291472.001600",
        "parent_user_id": "UGF7MRWMS"
    }

    slack_side_of_first_comment_from_zendesk = {
        "bot_id": "B01ADD673UL",
        "type": "message",
        "text": "(Zendesk): first comment from zendesk",
        "user": "U01AKS3HDJ5",
        "ts": "1608291667.001900",
        "team": "TGFJG8VEZ",
        "bot_profile": {
            "id": "B01ADD673UL",
            "deleted": False,
            "name": "ZenSlackChat",
            "updated": 1599473694,
            "app_id": "A01A748235G",
            "icons": {
                "image_36": "https://a.slack-edge../bot_36.png",
                "image_48": "https://a.slack-edge../bot_48.png",
                "image_72": "https://a.slack-edge../service_72.png"
            },
            "team_id": "TGFJG8VEZ"
        },
        "thread_ts": "1608291472.001600",
        "parent_user_id": "UGF7MRWMS"
    }


    zendesk_side_of_first_comment_from_slack = {
        "attachments": [],
        "author_id": 375202855898,
        "body": "Oisin Mulvihill (Slack): first comment from slack",
        "created_at": "2020-12-18T11:44:40Z",
        "id": 738394825737,
        "public": True,
        "type": "Comment",
        "html_body": "<...>",
        "plain_body": "Oisin Mulvihill (Slack): first comment from slack",
        "audit_id": 738394825577,
        "metadata": {
            "custom": {},
            "system": {
                "client": "Zenpy/2.0.10",
                "ip_address": "1.2.3.4",
                "latitude": 52.0,
                "location": "ENG, United Kingdom",
                "longitude": 0.0
            }
        },
        "via": {
            "channel": "api",
            "source": {
                "from_": None,
                "rel": None,
                "to": {},
                "from": {}
            }
        }
    }
    # There should be no difference now:
    assert messages_for_slack(
        slack_issue + [
            first_slack_comment,
            slack_side_of_first_comment_from_zendesk
        ], 
        [
            zendesk_with_link_to_slack,
            first_comment_from_zendesk,
            zendesk_side_of_first_comment_from_slack
        ]
    ) == []
    