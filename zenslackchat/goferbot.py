# The slackbot library is very good if you want to respond to commands
import re

from slackbot.bot import Bot
from slackbot.bot import respond_to
from slackbot.bot import default_reply


@respond_to(matchstr=r'^.*$', flags=0)
def respond_to_all(message):
    message.reply('Everything is not bad at the moment.', in_thread=True)

@default_reply()
def default_respond_to_all(message):
    message.reply('Everything is not bad at the moment.', in_thread=True)


def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()