from unittest.mock import patch

import pytest

from zenslackchat import slack_utils


def test_slack_api_env_config():
    """Verify the Slack config env variables.
    """
    # make sure no SLACK_* variables are set to interfere with test.
    with patch.dict('os.environ', {}, clear=True):    
        # Check we raise an exception if the token is not set.
        with pytest.raises(ValueError):
            config = slack_utils.config()    

    # do we handle set but empty?
    with patch.dict('os.environ', {'SLACKBOT_API_TOKEN': ' '}, clear=True):    
        with pytest.raises(ValueError):
            config = slack_utils.config()    

    mock_env = {'SLACKBOT_API_TOKEN': 'token1234'}
    with patch.dict('os.environ', mock_env, clear=True):    
        config = slack_utils.config()    

    assert config['token'] == 'token1234'


def test_slack_message_url():
    """Verify the URL generated to point at (UI not API) ticket in zendesk.
    """
    # Test the conversion of the ID to its URL form
    chat_id = '1597935682.010800'
    env = {'SLACK_WORKSPACE_URI': 'https://example.com/'}
    with patch.dict('os.environ', env, clear=True):    
        url = slack_utils.message_url('C018JUAGGTS', chat_id)
    assert url == 'https://example.com/C018JUAGGTS/p1597935682010800'

    # default: nothing set in env
    with patch.dict('os.environ', {}, clear=True):    
        url = slack_utils.message_url('channel', 'message123')
    assert url == 'https://slack.example.com/archives/channel/pmessage123'

    # check trailing and non-trailing slash set
    env = {'SLACK_WORKSPACE_URI': 'https://example.com/'}
    with patch.dict('os.environ', env, clear=True):    
        url = slack_utils.message_url('456', '123')
    assert url == 'https://example.com/456/p123'

    env = {'SLACK_WORKSPACE_URI': 'https://example.com'}
    with patch.dict('os.environ', env, clear=True):    
        url = slack_utils.message_url('ASK323K','QWD42D')
    assert url == 'https://example.com/ASK323K/pQWD42D'
