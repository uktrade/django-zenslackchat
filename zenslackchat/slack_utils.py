"""
Code to help me work with slack messaging.

Oisin Mulvihill
2020-08-18

"""
import os
import pprint
import logging

from slack.errors import SlackApiError

from zenslackchat import zendesk_api


def config():
    """Recover the slack configuration from the environment.

    The SLACKBOT_API_TOKEN must be set or ValueError will be raised.

    """
    token = os.environ.get("SLACKBOT_API_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Required environment variable not set: SLACKBOT_API_TOKEN "
        )

    return dict(
        token=token
    )

def message_url(channel, message_id):
    """Return a direct link to the message that can be stored in zendesk.

    This expects the environment variable SLACK_WORKSPACE_URI to be set. 

    """
    SLACK_WORKSPACE_URI = os.environ.get(
        'SLACK_WORKSPACE_URI', 
        'https://slack.example.com/archives'
    )

    # Convert to the ID slack uses on the web.
    # e.g. 1597844917.045900 -> p1597844917045900
    msg_id = 'p{}'.format(message_id.replace('.', ''))

    # handle trailing slash being there or not (urljoin doesn't).
    return '/'.join([SLACK_WORKSPACE_URI.rstrip('/'), channel, msg_id])


def post_message(client, chat_id, channel_id, message):
    """Send a message to the parent thread with an update.

    This is also a handy function to aid mocking in tests.

    """
    return client.chat_postMessage(
        channel=channel_id,
        text=message,
        thread_ts=chat_id
    )


def message_handler(payload):
    """Decided what to do with the message we have received.
    """
    p = pprint.pformat(payload)
    logging.debug(f'Payload received:\n{p}\n')

    # Fields that must be present for this to work:
    web_client = payload['web_client']
    data = payload['data']
    channel_id = data['channel']
    text = data.get('text', '')

    if 'bot_id' in data:
        # This is usually us/a bot posting a reply to a message or thread. 
        # Without this we would end up in a loop replying to ourself.
        logging.debug(f"Ignoring bot <{data['bot_id']}> message: {text}")
        return

    subtype = data.get('subtype')
    if subtype in ['message_changed', 'message_deleted']:
        # Deleted messages I don't think I care about. Messages deleted inside
        # a thread show up as changed. Again I'm not sure I care it might be 
        # more work than its worth to keep up with these.
        logging.debug(f"Ignoring subtype '{subtype}': {text}\n")
        return

    user_id = None
    if 'message' in data:
        # reply
        text = data['message'].get('text', '')
        user_id = data['message']['user']

    else:
        user_id = data.get('user')
        
    if user_id:
        # Recover the slack channel message author's email address. I assume 
        # this is always set on all accounts.
        logging.debug(f"Recovering profile for user <{user_id}>")
        resp = web_client.users_info(user=user_id)
        recipient_email = resp.data['user']['profile']['email']

    # ID for parent message, thread_ts is ID for message under the parent.
    chat_id = data.get('ts', '')
    thread_id = data.get('thread_ts', '')

    # There is a https://api.slack.com/events/message/message_replied event,
    # however its not reliable apparently due to a bug. The recommended 
    # for thread dection is to check the ts (chat_id)/thread_ts (thread_id) 
    # which I do. From observation this seems to work well.
    #
    if chat_id and thread_id:
        # This is a new message in a thread, but not from a bot.
        #
        # Handle thread commands here e.g. done/reopen
        #
        url = message_url(channel_id, chat_id)
        logging.debug(
            f"Received thread message from '{recipient_email}': {text}\n"
        )

        # Hmm, I'm seeing timeouts possibly due to rate limiting
        #
        # DEBUG:zenpy.lib.api:GET: https://oisinmulvihillhelp.zendesk.com/api/v2/search.json?query=1597849566.053700%20type%3Aticket - {'timeout': 60.0}
        # DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): oisinmulvihillhelp.zendesk.com:443
        # DEBUG:urllib3.connectionpool:https://oisinmulvihillhelp.zendesk.com:443 "GET /api/v2/search.json?query=1597849566.053700%20type%3Aticket HTTP/1.1" 200 None
        # DEBUG:zenpy.lib.api:SearchResponseHandler matched: {'results': [], 'facets': None, 'next_page': None, 'previous_page': None, 'count': 0}
        #
        # How should I handle? Is it really an issue on an enterprise version 
        # of Zendesk. I'm just using the free version.
        #
        ticket = zendesk_api.get_ticket(chat_id)
        if ticket:
            logging.debug(
                f'Recoverd ticket {ticket.id} from slack thread {url}'
            )
            command = text.strip().lower()
            if command == 'done':
                # Time to close the ticket as the issue has been resolved.
                logging.debug(
                    f'Closing ticket {ticket.id} from slack thread {url}.'
                )
                zendesk_api.close_ticket(chat_id)
                post_message(
                    web_client, chat_id, channel_id, 'Ticket closed.'
                )

        else:
            # This could be an old thread pre-bot days:
            logging.warn(f'No ticket found in slack thread {url}. Old thread?')

    elif chat_id:
        # A potentially new message (not in a thread):
        logging.debug(
            f"Received message from '{recipient_email}': {text}\n"
        )

        # I'll use the parent conversation as the ID and tie the ticket 
        # back to this. I'll use Zendesk as the "backend" store.

        # New issue: generate Zendesk ticket
        slack_chat_url = message_url(channel_id, chat_id)

        if not zendesk_api.get_ticket(chat_id):
            # No clear to create.
            ticket = zendesk_api.create_ticket(
                chat_id=chat_id, 
                recipient_email=recipient_email, 
                subject=text, 
                slack_message_url=slack_chat_url,
            )
            # Once-off response to parent thread:
            url = zendesk_api.zendesk_ticket_url(ticket.id)
            message = f"Hello, your new support request is {url}"
            post_message(web_client, chat_id, channel_id, message)

        else:
            logging.info(
                f"The issue '{text}' is already in Zendesk '{chat_id}'"
            )