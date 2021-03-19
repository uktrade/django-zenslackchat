from unittest.mock import MagicMock

from zenslackchat import slack_api


def test_slack_message_url(log):
    """Verify the URL generated to point at (UI not API) ticket in zendesk.
    """
    # Test the conversion of the ID to its URL form
    workspace_uri = 'https://example.com/'
    chat_id = '1597935682.010800'
    url = slack_api.message_url(workspace_uri, 'C018JUAGGTS', chat_id)
    assert url == 'https://example.com/C018JUAGGTS/p1597935682010800'

    # check trailing and non-trailing slash set
    workspace_uri = 'https://example.com/'
    url = slack_api.message_url(workspace_uri, '456', '123')
    assert url == 'https://example.com/456/p123'

    workspace_uri = 'https://example.com'
    url = slack_api.message_url(workspace_uri, 'ASK323K','QWD42D')
    assert url == 'https://example.com/ASK323K/pQWD42D'



def test_slack_url_to_chat_id(log):
    """Verify the conversion from URL to chat ID.
    """
    chat_id = '1597935682.010800'
    url = 'https://example.com/C018JUAGGTS/p1597935682010800'
    result = slack_api.url_to_chat_id(url)
    assert result == chat_id

    chat_id = '1597935682.010800'
    url = 'https://example.com/C018JUAGGTS/p1597935682010800/'
    result = slack_api.url_to_chat_id(url)
    assert result == chat_id

    chat_id = ''
    url = ''
    result = slack_api.url_to_chat_id(url)
    assert result == chat_id


def test_post_message(log):
    """Verify the URL generated to point at (UI not API) ticket in zendesk.
    """
    mock_web_client = MagicMock()

    slack_api.post_message(
        mock_web_client, 'chat_id_12', 'channel_id_32', 'hello dude!'
    )

    mock_web_client.chat_postMessage.assert_called_with(
        channel='channel_id_32',
        text='hello dude!',
        thread_ts='chat_id_12'
    )
