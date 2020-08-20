"""
Main

"""
import sys
import pprint
import logging
import logging.config

from slack import RTMClient

from zenslackchat import message
from zenslackchat import botlogging
from zenslackchat.slack_utils import config




@RTMClient.run_on(event='message')
def react_to(**payload):
    """Pass the payload on to the message handler.

    This uses catchall try-except to catch exceptions and log them. Without 
    this they are silently hidden from you. At least with try-except I can 
    log what went wrong.

    """
    log = logging.getLogger('zenslackchat')
    try:
        p = pprint.pformat(payload)
        log.debug(f'Payload received:\n{p}\n')
        message.handler(payload)
        
    except:
        log.exception("Slack message_handler error: ")


def main():
    """Run the zenslackbot until interrupted.
    """    
    botlogging.log_setup()
    log = logging.getLogger('zenslackchat')
    token = config()['token']
    log.info(f"Started.")
    RTMClient(token=token).start()
    log.warning(f"Bot exited.")
    sys.exit(0)


if __name__ == "__main__":
    main()

    