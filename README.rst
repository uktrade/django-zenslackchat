Zenslackchat 
============

.. contents::

Helpdesk support using a slack chat bot and integration into zendesk.

I'm going to use GOV.UK PaaS for this so will need to look at buildpacks and
cloud foundry to aid me with this.

- https://docs.cloud.service.gov.uk/deploying_apps.html#deploying-apps

I'm using make, docker-compose, python3 and virtualenvwrappers to develop the 
project locally. I currently work of Mac OSX for development and use Homebrew 
to install what I need. Your mileage may vary.


Spike Investigation
-------------------

I've converted to a Django project as I needed proper storage. Zendesk 
external_id hack wasn't working. The advantage of going Django is I can have
a single app now which subscribes to events and handles Slack and Zendesk 
OAuth.

Scenario / chat with Matt / Things to work out on SRE-725:

- user types in question on the slack channel (without /<command> ideally).
   - OM: I'm using slack client and subscribing to message events. I get *all* 
     the messages including my own. I then have control over how to react, 
     although its a bit tricky.
- Bot instantly replies in a thread that this got assigned a ticket ID X. Ticket is stored in Zendesk
   - OM: I've got this working as requireds.
- Ticket in zendesk filled in with end user email so that user gets updated on the progress. 
   - OM: I recover the slack message author's email. I then add this as the recipient when creating the ticket. I'll need to see how this works in the field.
- Record URL to the conversation on slack
   - OM: |ss| Your can add URL to slack thread as a custom field on zendesk. |se|
      - I can add a custom field. Then you need to find its unique ID. To set it you then user the custom_fields: [{'id': <id>, 'value': '...'}]. This is a bit unweildy.
      - When you set this in the code, it does populate the text box with the link however it is not clickable. I didn't see a HTML link option as a field.
   - OM: A better approach (in my view) I've added the link as the first ticket_comment. This is clickable and opens slack to reveal the message thread.
- SRE on call follows up with the conversation on slack
- Bot replicates the conversation into zendesk ticket
   - OM: I'll need to look into webhooks at least for the zendesk to slack replication. So new comments in zendesk trigger the bot to put them in the slack chat.
- SRE on call closes the ticket by typing “done” or similar within the thread
   - OM: This works now, it could be any string. Maybe done is too vague. Should anyone be able to type "done" to close the issue?
- Can we avoid /<command> actions?
  - OM: yes there is not need for these.
- Ticket assigned to every thread.
  - Webops metrics time open/cycle time.
     - OM: Zendesk does have metrics, have to investigate.
     - OM: Bot could reply with stats in response to query.
     - OM: Now I also have opened/closed datetimes on issues in my DB. So you 
       could generate reports for this.
  - Primary/Secondary people on support added to ticket.
     - If you had a way to query some API for who is "on call", this could be 
       added automatically as Ticket assignees.

Todo
~~~~

Zendesk / Slack investigation.
 - [X] |ss| Get access credentials for API access to a Zendesk |se|
 - [X] |ss| Choose a python Zendesk |se| 
 - [x] |ss| Create a zendesk ticket and investigate structure |se| 
 - [x] |ss| Slackbot reading |se|
 - [x] |ss| Skeletal slackbot and slack integration |se|
 - [X] |ss| Can bot respond to a user without using a slack command? |se|
 - [X] |ss| Can bot respond in a thread? |se|
 - [X] |ss| link from slack to zendesk in the thread |se|
 - [X] |ss| link from zendesk UI to the slack message |se|
 - [X] |ss| Close the issue on slack by saying 'done' in the thread |se|
 - [X] |ss| Ship conversation messages from slack to zendesk |se|
 - [X] |ss| Ship messages from zendesk to slack |se|
 

Zendesk
~~~~~~~

For Zendesk integration you need to enable and generate a token (not oauth):
 - https://support.zendesk.com/hc/en-us/articles/226022787-Generating-a-new-API-token-

The token approach is functional, however its permissons are too broad using 
this method. To get off the ground its fine, but we'll need to move to OAuth
in production. I'll move to this as I'm done this for Slack.

Zendesk OAuth:
- https://support.zendesk.com/hc/en-us/articles/203663836-Using-OAuth-authentication-with-your-application

Useful Reference docs:

- https://developer.zendesk.com/rest_api/docs/support/tickets#json-format
- https://developer.zendesk.com/rest_api/docs/support/ticket_comments
- Zenpy: http://docs.facetoe.com.au/api_objects.html
- http://docs.facetoe.com.au/zenpy.html


This is the raw set up you need to enable comment shipping to slack from 
Zendesk. 

HTTP Target
```````````

You need to create a HTTP target which can then be used in the trigger set up. 
From https://<your zendesk>.zendesk.com/agent/admin/extensions you click 
"add target" and then set:

- Title: zenslackchat zendesk comment notification
- URL: <Ngrok.io URI or Production URI>/zendesk/webhook
- Method: POST
- Check basic auth
  - username: webhook_access
  - password: <shared with webapp>

You can test the target if you have set up the end point in advance. Otherwise
just select "Create Target" in the drop down. and move on to creating the 
trigger for this HTTP target. More detail on how to set up a webhook can be
found in the Zendesk:
- https://support.zendesk.com/hc/en-us/articles/204890268-Creating-webhooks-with-the-HTTP-target


Comment Trigger
```````````````

You need to create a trigger https://<your zendesk>.zendesk.com/agent/admin/triggers/<trigger id>
and then do the following set up:

- Trigger name: ticket-comment
- Description: Ticket Comment that should be sent to zenslackchat
- Meet any condition: 
  - "comment text"
  - "Does not contain the following string"
  - "resolve request"
- Actions
  - Notifiy target
  - Select the trigger created earlier
  - Set the JSON body set up::
   {
      "external_id": "{{ticket.external_id}}",
      "ticket_id": "{{ticket.id}}"
   }

The "meet any condition" is a bit of a hack to get comments sent to us.


Webhook
```````

Sign-up for a free Ngrok.io account. This allows you to have a public 
accessible HTTP endpoint to your local instance for development. Run ngrok
locally as follows::

   ngrok http 12380

This should then give you a URL you can use in the HTTP Target. For example 
http://ed8a1df2e030.ngrok.io. This changes each time its restarted so you will
need to update the HTTP Target when this happens.

The webhook code is now integrated into the Django webapp. Running locally its
found on "http://localhost:8000/zendesk/webhook/"


Slack
~~~~~

I've ditched the standalone bot and favour of using Django and subscribing a
specific view to receive events. Django+Rest Framework projects are quite 
common here so others can easily work on this project too.

You need to create a Slack app
``````````````````````````````

Go to https://api.slack.com/apps and create a slack app.

New App:
- app name: ZenSlackChat
- Development Slack Workspace: <workspace>

Now I need from the App Credentials
- Client ID
- Client Secret
- Signing Secret
- Verification Token

Display Information
- App Name: zenslackchat

OAuth & Permissions
Tokens for Worksapce
- OAuth Access Token
- Bot User OAuth Access Token

Redirect URLs
- https://<location of running endpoint>/slack/oauth/

Scopes

Bot Token Scopes: 
- channels:history
- groups:history
- users:read
- users:read.email

User Token Scopes
  - channels:history
    View messages and other content in the user’s public channels

Event Subscriptions
- Enable Events: on
- Request URL: https://<location of running endpoint>/slack/events/


django-zenslackchat
-------------------

To run the webapp locally::

    workon zenslackchat

    # Needed in production. If not given this is randomly generated each time.
    export WEBAPP_SECRET_KEY=<some key>

    # Hostname of where its running (added to allowed hosts):
    export PAAS_FQDN=

    # Set up the credentials:
    # zendesk
    export ZENDESK_EMAIL=<user on support site> 
    export ZENDESK_SUBDOMAIN=<support site subdomain>
    export ZENDESK_TOKEN=<zendesk token> 
    export ZENDESK_TICKET_URI=https://<support site>.zendesk.com/agent/tickets

    # slack
    export SLACK_CLIENT_ID=<slack app oauth client id>
    export SLACK_CLIENT_SECRET=<slack app oauth client secret>
    export SLACK_VERIFICATION_TOKEN=<slack app verification token>
    export SLACK_SIGN_SECRET=<slack app sign secret>
    export SLACK_BOT_USER_TOKEN=<slack app bot user token>
    export SLACK_WORKSPACE_URI=https://<workspace>.slack.com/archives
        
    # Run the bot (Python3)
    python manage.py runserver


Development
-----------

To set up the code for development you can do::

    mkvirtualenv --clear -p python3 zenslackchat
    make install

To run the service locally in the dev environment do::

    # activate the env
    workon zenslackchat

    # run the webapp
    make run

Testing
-------

With docker compose running postgres in one window, you can run the tests as
follows::

    # activate the env
    workon zenslackchat

    # Run basic model and view tests
    make test


.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>