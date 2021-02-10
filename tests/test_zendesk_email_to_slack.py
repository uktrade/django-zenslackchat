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
from zenslackchat.message_tools import message_issue_zendesk_url
from zenslackchat.zendesk_email_to_slack import email_from_zendesk


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


@patch('zenslackchat.zendesk_email_to_slack.get_ticket')
@patch('zenslackchat.zendesk_email_to_slack.add_comment')
@patch('zenslackchat.zendesk_email_to_slack.message_issue_zendesk_url')
@patch('zenslackchat.zendesk_email_to_slack.message_who_is_on_call')
@patch('zenslackchat.zendesk_email_to_slack.SlackApp')
@patch('zenslackchat.zendesk_email_to_slack.ZendeskApp')
def test_email_from_zendesk_is_added_for_tracking(
    ZendeskApp, SlackApp, message_who_is_on_call, message_issue_zendesk_url, 
    add_comment, get_ticket, log, db
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
    ticket = FakeTicket(
        ticket_id='32',
        subject='My printer is on 🔥',
        description='I was smoking next to it and it just went up.'
    )
    get_ticket.return_value = ticket

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
    settings = dict(
        DEBUG=True, 
        SRE_SUPPORT_CHANNEL=channel_id,
        ZENDESK_USER_ID='1234',
        ZENDESK_GROUP_ID='7890',
        ZENDESK_TICKET_URI='https://z.e.n.d.e.s.k',
        SLACK_WORKSPACE_URI='https://s.l.a.c.k',
    )
    with patch.dict('webapp.settings.__dict__', settings, clear=True):
        email_from_zendesk(event, slack_client, zendesk_client)

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

    # Check the args to the call that would post a message:
    message_issue_zendesk_url.assert_called_with(
        slack_client,
        'https://z.e.n.d.e.s.k',
        '32',
        '1597940362.013100',
        'C024JUTACTS'
    )

    # No pager duty configured so no message about this:
    message_who_is_on_call.assert_called_with(
        {}, slack_client, '1597940362.013100', 'C024JUTACTS'
    )

    # Zendesk issue will be updated with link to slack issue SRE team looks at
    slack_chat_url = 'https://s.l.a.c.k/C024JUTACTS/p1597940362013100'
    add_comment.assert_called_with(
        zendesk_client, ticket, 
        f'The SRE team is aware of your issue on Slack here {slack_chat_url}.'
    )
