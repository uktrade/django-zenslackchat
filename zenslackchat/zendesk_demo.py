# Figure out how to create amd update tickets using an API token.
#
import os
import random
import datetime

from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket
from zenpy.lib.api_objects import Comment

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

# Recover my details, these always seem to return something even if auth
# isn't correct. In that case its just an 'Anonymous User'.
me = zenpy_client.users.me()
print(f'Me: {me.name}')

# See other users on the system:
for user in zenpy_client.users():
    print(f'User: {user.name}')

# See all the current tickets:
for ticket in zenpy_client.tickets():
    print(ticket)

# To be a new ticket it seems the subject needs to change or it will cause
# create to error

# make subject different each time
random = int(random.random() * 10000)

issue = Ticket(
    type='question', 
    subject=f'Killer ☎️  {random} is loose and hungry!', 
    requestor_id=me.id,
    comment=Comment(
        body='Its eating people in the office 🐙',
        author_id=me.id
    )
)
ticket_audit = zenpy_client.tickets.create(issue)
ticket = ticket_audit.ticket
ticket_id = ticket.id
print(
    f'Your case number for issue "{issue.subject}" is "'
    f'{ticket_id}'
    '". Thanks!'
)

# Add another comment to the existing ticket
ticket.tags = ['concerning']
ticket.comment = Comment(
    body='No, really, its becomming a serious concern now! 🚀',
    author_id=me.id
)
ticket_audit = zenpy_client.tickets.update(ticket)

#



