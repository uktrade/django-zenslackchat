# Figure out how to create tickets using an API token. I might need to move
# to oauth token instead, we'll see.
#
import os
import base64
import datetime

import zenpy
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, Comment

email = os.environ.get('ZENDESK_EMAIL', '<email@example.com>')
token = os.environ.get('ZENDESK_TOKEN', '<token>')
subdomain = os.environ.get('ZENDESK_SUBDOMAIN', '<something>')

# Token access : to broad a permission set.
#
# I need to come back around on this. OAuth might be a better approach as it
# looks like you can restrict the scope/access much more. Its just a pain as
# you will have to create an app and do the two step request/access token 
# dance.
#
# https://support.zendesk.com/hc/en-us/articles/
#   203663836-Using-OAuth-authentication-with-your-application
#
zenpy_client = Zenpy(
    email=email,
    token=token,
    subdomain=subdomain,
)

me = zenpy_client.users.me()
print(f'Me: {me.name}')

for user in zenpy_client.users():
    print(f'User: {user.name}')

yesterday = datetime.datetime.now() - datetime.timedelta(days=7)
today = datetime.datetime.now()
# query = zenpy_client.search(
#     "zenpy", 
#     created_between=[yesterday, today], 
#     type='ticket', 
#     minus='negated'
# )
query = zenpy_client.tickets()
for ticket in query:
    print(ticket)