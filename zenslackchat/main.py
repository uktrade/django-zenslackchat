import os

import zenpy
import requests

creds = {
    'email': os.environ.get('ZENDESK_EMAIL', '<email>'),
    'token':  os.environ.get('ZENDESK_TOKEN', '<token>'),
    'subdomain': os.environ.get('ZENDESK_SUBDOMAIN', '<subdomain>')
}

from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, Comment

print(f'Credentials: {creds}')
zenpy_client = Zenpy(**creds)

print('Users:')
print(zenpy_client.users())

print(
    zenpy_client.tickets.create(
        Ticket(subject="Important", description="Thing")
    )
)
