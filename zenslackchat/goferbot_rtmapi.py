#
# Based on article from:
# 
#  https://medium.com/@rdcolema7/
#      building-a-python-slackbot-that-actually-works-2930663e20f3
#
#
import os
import sys
import pprint
import logging

from slack import RTMClient
from slack.errors import SlackApiError


def message_handler(payload):
    """
    """
    p = pprint.pformat(payload) if payload else '<none>'
    print(f'Payload:\n{p}\n')
    
    data = {}
    channel_id = '?'
    if 'data' in payload:
        data = payload['data']
        channel_id = data['channel']

    text = ''
    if 'text' in data:
        text = data['text']

    if 'bot_id' in data:
        # This is usually this bot post a reply to a message or thread. Without
        # this we end up in a loop replying to ourself.
        print(f"Ignoring bot <{data['bot_id']}> message: {text}")
        return

    subtype = ''
    if 'subtype' in data:
        subtype = data['subtype']

    message = {}
    if 'message' in data:
        message = data['message']
    
    thread_ts = data.get('thread_ts', '')

    if subtype == 'message_replied':
        if 'bot_id' in  message:
            # This is usually this bot posting an in-thread reply to a message 
            # Without this we end up in a loop replying to ourself.
            print(f"Ignoring bot <{data['bot_id']}> message: {text}")
            return

        thread_ts = message.get('thread_ts', '')
        # I notice the original message is here in a reply. Recover it to aid
        # logging.
        #
        # blocks': [
        #     {'elements': [
        #         {'elements': [
        #             {'text': 'e'}
        #         ]}
        #     ]}
        # ]
        #
        thread_message = '?'
        blocks = message.get('blocks', [])
        if len(blocks) > 0:
            e0 = blocks[0]
            if 'elements' in e0:
                e1 = e0['elements']
                if len(e1) > 0:
                    if 'elements' in e1:
                        e2 = e1['elements']
                        if len(e2) > 0:
                            if 'text' in e2:
                                thread_message = e2['elements']                        

        # a reply to a message
        m = message.get('text') or '<none>'
        print(f"In Reply to \"{thread_message}\":\n{m}\n")
        message = "Hello, I've added your comment to <Zendesk Link>"

        ## Ship the new reply to the issue in Zendesk

    else:
        # a general message to the channel
        m = text or '<none>'
        print(f"New Support Request:\n{m}\n")
        message = "Hello, your new support request is <Zendesk Link>"

    web_client = payload['web_client']
    try:
        response = web_client.chat_postMessage(
            channel=channel_id,
            text=message,
            thread_ts=thread_ts
        )

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        # str like 'invalid_auth', 'channel_not_found'
        assert e.response["error"]  
        print(f"Got an error: {e.response['error']}")

    else:
        print(f"Response to postMessage: {response}")


@RTMClient.run_on(event='message')
def react_to(**payload):
    """Pass the payload on to the message handler.

    This use catch-all try-except to catch exceptions and log them. Without 
    this they are hidden from you. You see nothing happening. At least with
    try-except I can see what went wrong.

    """
    try:
        message_handler(payload)
    except:
        logging.exception("Message Handler Fail: ")


def main():
    RTMClient(token=os.environ["SLACKBOT_API_TOKEN"]).start()
    logging.warning(f"Slackbot exit.")
    sys.exit(0)


if __name__ == "__main__":
    main()

    