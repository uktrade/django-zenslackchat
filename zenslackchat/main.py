"""
Main

"""
import sys
import logging

from slack import RTMClient

from zenslackchat import slack_utils


@RTMClient.run_on(event='message')
def react_to(**payload):
    """Pass the payload on to the message handler.

    This uses catchall try-except to catch exceptions and log them. Without 
    this they are silently hidden from you. At least with try-except I can 
    log what went wrong.

    """
    try:
        slack_utils.message_handler(payload)
        
    except:
        logging.exception("Slack message_handler error: ")


def main():
    """
    """
    logging.basicConfig(level=logging.DEBUG)

    logging.info(f"Zenslackchat getting config for slack.")
    token = slack_utils.config()['token']

    logging.info(f"Zenslackchat started.")
    RTMClient(token=token).start()

    logging.warning(f"Zenslackchat bot exit.")
    sys.exit(0)


if __name__ == "__main__":
    main()

    