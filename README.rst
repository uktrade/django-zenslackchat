Zenslackchat 
============

.. image:: docs/zenslackchat-overview.png
    :align: center

The support team work through Slack. Zendesk is the company support issue tracking system. This bot will put new support issues raised on Slack into Zendesk. It will also update the conversation in Zendesk as it develops on Slack. If any comments are made on the issue in Zendesk these will also be sent to the support message thread on Slack. The idea is to pull in support requests from other platforms such as Microsoft Teams and the support Email in future.

The bot reports daily on the total amount of open issues and the total closed issues. The closed issue count represents only issues closed in the previous day. The previous day is worked out from the current day in which the report is run. Currently the bot posts the daily report on the support channel is monitors.

The bot needs to be installed as a Slack application using OAuth. The bot also needs to be told the channel it must monitor for support request messages.

To use the Zendesk API the bot must be registered as a OAuth application. Zendesk has extra set up around what comments get sent to Slack. Zendesk is set up to only notify the bot of comments from issue belonging to a certain support group. This prevents all Zendesk comments being sent to the bot.

The bot manages the issues raised using its own Postgres database. This allows for easy tracking and later reporting.

The bot is a Django web application. It uses Celery and Redis to schedule the periodic report.


.. contents::


Development
-----------

I'm using make, docker-compose, python3 and virtualenvwrappers to develop the 
project locally. I currently work of Mac OSX for development and use Homebrew 
to install what I need. Your mileage may vary.

To set up the code for development you can do::

   mkvirtualenv --clear -p python3 zenslackchat
   make test_install

There is a ``make install``. This only installs the apps dependancies and not 
those needed for testing.

To run the service locally in the dev environment do::

   # activate the env
   workon zenslackchat

   # run dependant services via docker compose (in its own terminal)
   make up

   # run the periodic task manager (in its own terminal)
   make runbeat

   # run the periodic task manager (in its own terminal)
   make runworker

   # run the webapp (in its own terminal)
   make runserver

Using the Makefile to run the webapp/worker/beat is only meant for local 
development. It is not for live environment use (staging/production/...)


Testing
~~~~~~~

You can run the tests as follows::

   # activate the env
   workon zenslackchat

   # run dependant services via docker compose (in its own terminal)
   make up

   # Run all tests and output a coverage report
   make test


Zendesk Set-up
--------------

Useful Reference docs:

- https://developer.zendesk.com/rest_api/docs/support/tickets#json-format
- https://developer.zendesk.com/rest_api/docs/support/ticket_comments
- Zenpy: http://docs.facetoe.com.au/api_objects.html
- http://docs.facetoe.com.au/zenpy.html


OAuth Registration
~~~~~~~~~~~~~~~~~~

For you Zendesk go to https://<subdomain>.zendesk.com/agent/admin/api/oauth_clients

- "Add OAuth Client"
- Client Name: ZenSlackChat
- Description: Ferry messages back and forth between Slack and Zendesk.
- Unique Identifier: zenslackchat
- Redirect URLS: https://<endpoint address>/zendesk/oauth/

The Unique Identifier is set as ZENDESK_CLIENT_IDENTIFIER in the webapp's 
environment. When you add the client a secret will be generated and shown once. This is set as ZENDESK_CLIENT_SECRET

Reference:

- https://support.zendesk.com/hc/en-us/articles/203663836-Using-OAuth-authentication-with-your-application


HTTP Target
~~~~~~~~~~~

You need to create a HTTP target which can then be used in the trigger set up. 
From ``https://<your zendesk>.zendesk.com/agent/admin/extensions`` you click 
"add target" and then set:

- Title: zenslackchat zendesk comment notification
- URL: <Ngrok.io URI or Production URI>/zendesk/webhook
- Method: POST

You can test the target if you have set up the end point in advance. Otherwise
just select "Create Target" in the drop down. and move on to creating the 
trigger for this HTTP target. More detail on how to set up a webhook can be
found in the Zendesk:

- https://support.zendesk.com/hc/en-us/articles/204890268-Creating-webhooks-with-the-HTTP-target


Zendesk Agent
~~~~~~~~~~~~~

Create an agent account the bot will assign tickets to. From 
https://<subdomain>.zendesk.com/agent/admin/people select "add user":

- Name: zenslackchat
- Email: <email address>
- Role: Agent

From the URL of the created user you will see the ID. This needs to be set as
ZENDESK_USER_ID in the webapp's environment.


Zendesk Group
~~~~~~~~~~~~~

Create an group which the bot agent is part of. From 
https://<subdomain>.zendesk.com/agent/admin/people select "add group":

- Group name: ZenSlackChat
- Group description: The group the ZenSlackChat bot uses to filter comments from.
- Agents in group: zenslackchat

From inspecting the page of the group you will see the ID. This needs to be set 
as ZENDESK_GROUP_ID in the webapp's environment.


Comment Trigger
~~~~~~~~~~~~~~~

You will need to create the ZenSlackChat group if its not present already. You 
need to create a trigger and then do the following set up:

- Trigger name: zenslackchat-ticket-comment
- Description: Trigger which will post comments to Zenslackchat for consideration.
- Meet ALL of the following conditions

   - Group is ZenSlackChat 

- Meet any condition: 

   - "comment text"
   - "Does not contain the following string"
   - "resolve request"

- Actions

   - Notifiy target
   - Select the trigger created earlier
   - Set the JSON body set up::

   {
      "token": "<shared secret token>",
      "chat_id": "{{ticket.external_id}}",
      "ticket_id": "{{ticket.id}}"
   }

The token is a shared random string that is set in the JSON body. This must 
match the value in the webapp's environment variable ZENDESK_WEBHOOK_TOKEN. If
these don't match the webhook request will be rejected and logged as an error.

The "meet any condition" is a bit of a hack to get comments sent to us. I would 
also put the trigger order first above any existing triggers although thats 
just me.


Webhook
~~~~~~~

The webhook code is integrated into the Django webapp. Running locally its
found on "http://localhost:8000/zendesk/webhook/"


OAuth
~~~~~

You need a paid Ngrok.io account to tunnel locally, as Zendesk requires a HTTPS
endpoint for the OAuth process. Locally the this runs on 
"http://localhost:8000/zendesk/oauth/"


Slack Set-up
------------

You need to create a Slack application in your workspace. Go to https://api.slack.com/apps 
and create a slack app.

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

- Tokens for Worksapce

  - OAuth Access Token
  - Bot User OAuth Access Token

- Redirect URLs

  - ``https://<location of running endpoint>/slack/oauth/``

Scopes

Bot Token Scopes: 

- channels:history
- groups:history
- chat:write
- users:read
- users:read.email

User Token Scopes

- channels:history

Install the app into workspace after set up the Scopes

- Accept the permissions
- Get the Bot user access token.

Event Subscriptions

- Enable Events: on
- Request URL: ``https://<location of running endpoint>/slack/events/``
- Subscribe to events on behalf of users: 

  - messages.channels

We don't need "Subscribe to bot events" or "App unfurl domains", so no set up
is needed.


Environment Variables
---------------------

WEBAPP_SECRET_KEY
~~~~~~~~~~~~~~~~~

If not given this is randomly generated each time. Changing this forces everyone 
to login again. 


DATABASE_URL
~~~~~~~~~~~~

This is set automatically by the PaaS environment when the running service is
linked to a Postgres instance. 

For local development the Makefile sets this to ``postgresql://service:service@localhost:5432/service``


REDIS_URL
~~~~~~~~~

This is set automatically by the PaaS environment when the running service is
linked to a Redis instance. For local development the Makefile sets this to ``redis://localhost/``


PAAS_FQDN
~~~~~~~~~

The fully qualified domain name of where the service is running. This is added
to the ALLOWED_HOSTS list.


Zendesk OAuth
~~~~~~~~~~~~~

For Zendesk OAuth you need to set the follow::

   export ZENDESK_CLIENT_IDENTIFIER=<oauth identifier>
   export ZENDESK_CLIENT_SECRET=<oauth secret>
   export ZENDESK_REDIRECT_URI=https://..host../zendesk/oauth/


ZENDESK_SUBDOMAIN
~~~~~~~~~~~~~~~~~

This is used by the code when setting up the API it uses. This is the name of 
the sub-domain from the zendesk URL i.e. in the URL ``https://<support_site>.zendesk.com``
the support_site is the sub domain. 


ZENDESK_TICKET_URI
~~~~~~~~~~~~~~~~~~

This is used as the base URL when generating links directly to Zendesk issues.
It takes the form ``https://<support site>.zendesk.com/agent/tickets``


ZENDESK_USER_ID
~~~~~~~~~~~~~~~

Who tickets are assigned to when the bot creates them. This is the numeric 
Zendesk ID for a user it will look something like ``375202855898``.


ZENDESK_GROUP_ID
~~~~~~~~~~~~~~~~

Which group tickets belong to. This is used when deciding what tickets the bot 
should handle. This is the numeric Zendesk ID for the group it will look 
something like ``360003877797``.


ZENDESK_WEBHOOK_TOKEN
~~~~~~~~~~~~~~~~~~~~~

This is a shared secret between the Zendesk HTTP target and the webapp's 
environment. It is a protection against unauthorised POSTs to the webapps 
endpoint.


Slack OAuth
~~~~~~~~~~~

You need to set the follow environment variable::
   
   SLACK_CLIENT_ID=<slack app oauth client id>
   SLACK_CLIENT_SECRET=<slack app oauth client secret>
   SLACK_SIGN_SECRET=<slack app sign secret>
   SLACK_VERIFICATION_TOKEN=<slack app verification token>


SLACK_WORKSPACE_URI
~~~~~~~~~~~~~~~~~~~

This is used as the base URL when generating links to created conversations on 
slack. The first comment on the newly created Zendesk issue will be a link back
to the conversation on Slack. The base URL look like ``https://<workspace>.slack.com/archives``


SRE_SUPPORT_CHANNEL
~~~~~~~~~~~~~~~~~~~

This is the slack channel ID which the bot will monitor for support request 
messages. Recovering this ID is not user friendly. It is a string that looks 
like ``C0192NP3TFG``.

The bot has the potential to receive *all* messages on slack, so the code 
rejects anything that does not come from this channel.


DISABLE_MESSAGE_PROCESSING
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is used to allow installing and running of the bot before its due to be
enabled. You can set up OAuth and other admin actions before going live.

When is set DISABLE_MESSAGE_PROCESSING=1, a warning will be logged for each 
message received indicating that it was not handled.


Development Environment Variables
---------------------------------

DISABLE_ECS_LOG_FORMAT
~~~~~~~~~~~~~~~~~~~~~~

By default JSON logging is used which is not user friendly when developing. To
logged a more user friendly format set the variables as follows::

   export DISABLE_ECS_LOG_FORMAT=1

When running via the make file this is set automatically.

DEBUG_ENABLED
~~~~~~~~~~~~~

**Warning**: Do not set this in a live environment. The system will log full 
Slack message events and other information, which may contain sensitive 
information.

By default DEBUG is disabled in Django settings. To enable DEBUG mode for 
development purposes set the variables as follows::

   export DEBUG_ENABLED=1

When running via the make file this is set automatically.

I have made this extra step of not allowing you to set DEBUG directly from the
environment, to slow you down and think before you set this.




.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>