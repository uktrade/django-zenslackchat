Zenslackchat
============

.. image:: docs/zenslackchat-overview.png
    :align: center

The support team work through Slack. Zendesk is the company support issue
tracking system. This bot will put new support issues raised on Slack into
Zendesk. It will also updates the conversation in Zendesk as it develops on
Slack. If any comments are made on the issue in Zendesk these will also be sent
to the support message thread on Slack. Email is support via Zendesk. New
emailed issues are set up as a new thread on the support Slack channel. In the
near future, issues Microsoft Teams will be integrated as well.

The bot reports daily on the total amount of open issues and the total closed
issues. The closed issue count represents only issues closed in the previous
day. The previous day is worked out from the current day in which the report is
run. Currently the bot posts the daily report on the support channel is monitors.

The bot needs to be installed as a Slack application using OAuth. The bot also
needs to be told the channel it must monitor for support request messages.

To use the Zendesk API the bot must be registered as an OAuth client. Zendesk
has extra set up around what comments get sent to Slack. Zendesk is set up to
only notify the bot of comments from issue belonging to a certain support
group. This prevents all Zendesk comments being sent to the bot.

The bot manages the issues raised using its own Postgres database. This allows
for easy tracking and later reporting.

The bot is a Django web application. It uses Celery and Redis to schedule the
periodic report.

This bot can connect to Pager Duty and recover an escalation policy from
which it then gets the primary and secondary contact names. If configured, who
is on call will be posted to the slack channel after an issue is raised.

.. contents::


Chat bot commands
-----------------

Any text sent to the chat bot will result in a new issues. In the new issue
thread, the bot will respond to the follow commands.

help
~~~~

This will list the available chat bot commands to the channel.


resolve | resolve ticket | ✅
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This will resolve the current issue based on the thread you are in. The issue
cannot be re-opened as Zendesk does not permit this.


Development
-----------

I'm using make, docker-compose, python3 and virtualenvwrappers to develop the
project locally. I currently work of Mac OSX for development and use Homebrew
to install what I need. Your mileage may vary. To set up the code for development
you can do::

   mkvirtualenv --clear -p python3 zenslackchat
   make test_install

There is a ``make install``. This only installs the apps dependancies and not
those needed for testing. To run the service locally in the dev environment do::

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


Upgrade Dependancies
~~~~~~~~~~~~~~~~~~~~

I use pip tools to manage the project dependancies https://github.com/jazzband/pip-tools.
The requirements.in is used as the unpinned source for dependancies. Add new
thing here. Then to update the requirements.txt you can do the following::

   # Install pip tools if needed and update the requirements:
   make pip-compile requirements.txt

   # Update the virtual environment:
   make install

Don't edit requirements.txt directly. Any changes will be lost when the file is
regenerated.


Zendesk Set-up
--------------

There are three main parts to set up in Zendesk. The first is to register the
OAuth client. This allows the webapp to use the Zendesk API. Next is setting up
the HTTP Target which POSTs comments to the webapp's /zendesk/webhook/ endpoint.
Finally you need to configure the comment trigger which decides what comments
should be sent to the webapp. Once accepted the comments will be sent to the
respective Slack conversations.

A ZenSlackChat user and group is used to restrict what gets sent to the bot.
Without these and their use in the comment trigger to filter, all Zendesk
comments would be sent to the webapp. This would risk exposing sensitive data
which should not go to the webapp.

Useful development reference docs:

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
environment. When you add the client a secret will be generated and shown once.
This is set as ZENDESK_CLIENT_SECRET. The redirect URL should be the same as
ZENDESK_REDIRECT_URI set for the webapp's env.

You kick off the OAuth process by going to the site root. Log-in and you will
see a section called "OAuth integrations for" and there is a Zendesk entry
and a link to "Add".

If you are developing locally you would need a paid Ngrok.io account to tunnel
the staging Zendesk to a local running webapp. Zendesk requires a HTTPS endpoint
for the OAuth process.

In local development this runs on:

- http://localhost:8000/zendesk/oauth/


Handy Zendesk OAuth client registration documentation:

- https://support.zendesk.com/hc/en-us/articles/203663836-Using-OAuth-authentication-with-your-application


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

   - Notifiy target -> zenslackchat-ticket-comment
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


Zendesk SRE Email Address
~~~~~~~~~~~~~~~~~~~~~~~~~

To create an issue via email and then tell ZenSlackChat about it, you must first
create an email address in Zendesk. Then the HTTP target and new email trigger
need to be created.

As admin go to https://<subdomain>.zendesk.com/agent/admin/email to add a new
email. The fillout the following details:

- Select "Add Address" -> "Create new Zendesk address"
- Enter the local part for the email for example sre or sre-staging.
- Click "Create Now"

Send an email to this address to verify it is working. Zendesk will create a
new issue for the received email, if it is working correctly.


New Email HTTP Target
~~~~~~~~~~~~~~~~~~~~~

You need to create a HTTP target which can then be used in the new email
trigger set up. From ``https://<your zendesk>.zendesk.com/agent/admin/extensions``
you click "add target" and then set:

- Title: zendesk-to-zenslackchat-email-event
- URL: <Ngrok.io URI, Staging or Production URI>/zendesk/email/webhook/
- Method: POST

You can test the target if you have set up the end point in advance. Otherwise
just select "Create Target" in the drop down. and move on to creating the
trigger for this HTTP target.


New Email Trigger
~~~~~~~~~~~~~~~~~

Now the email address and HTTP target are set up a trigger is needed to react
to new created issues via email. Go to ``https://<your zendesk>.zendesk.com/agent/admin/triggers``
and click "Add Trigger" filling out the following details:

- Trigger Name: zendesk-new-request
- Description: zendesk-new-request
- Meet All of the following conditions

   - Ticket Is Created
   - Status Is not Solved
   - Status Is not Closed
   - Channel Is Email
   - Received at Is <zendesk email created earlier>

- Actions

  - Notify target -> zendesk-to-zenslackchat-email-event
   - Set the JSON body set up::

   {
      "token": "<shared secret token>",
      "ticket_id": "{{ticket.id}}"
   }

The token is the same token set up for the comment trigger. See that for more
details.


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

You kick off the OAuth process by going to the site root. Log-in and you will
see a section called "OAuth integrations for" and there is a Slack entry and a
link to "Add".


PagerDuty OAuth
---------------

To set up a new OAuth client go to your account:

- https://<your subdomain>.pagerduty.com/developer/apps/register

For "Build an App" fill out

- App Name: ZenSlackChat
- Brief Description: Access to recover who is on call.
- Category: API Management
- Publish: no

Once you'd filled this out and saved the app you can go to the OAuth section

- https://<your subdomain>.pagerduty.com/developer/apps/<APP ID>/editOAuth

From here you can set up the redirect URLs and recover the client id and secret
you need to set in the environment.

You kick off the OAuth process by going to the site root. Log-in and you will
see a section called "OAuth integrations for" and there is a Pager Duty entry
and a link to "Add".


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


ZENDESK_AGENT_EMAIL
~~~~~~~~~~~~~~~~~~~

When Zendesk creates and issue, it imperonsates the ZenslackChat user. This is
the email address of that user and must match what is shown on the account.


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

ALLOWED_BOT_IDS
~~~~~~~~~~~~~~~~~~~

This is a comma separated list of Slack Bot IDs that are allowed to create tickets in
Zendesk.


DISABLE_MESSAGE_PROCESSING
~~~~~~~~~~~~~~~~~~~~~~~~~~

This is used to allow installing and running of the bot before its due to be
enabled. You can set up OAuth and other admin actions before going live.

When is set DISABLE_MESSAGE_PROCESSING=1, a warning will be logged for each
message received indicating that it was not handled.


PagerDuty OAuth
~~~~~~~~~~~~~~~

For PagerDuty OAuth you need to set the follow::

   export PAGERDUTY_CLIENT_IDENTIFIER=<oauth identifier>
   export PAGERDUTY_CLIENT_SECRET=<oauth secret>
   export PAGERDUTY_REDIRECT_URI=https://..host../pagerduty/oauth/
   export PAGERDUTY_ESCALATION_POLICY_ID=<policy id string>


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

When running via ``make run`` this is set automatically.

I have made this extra step of not allowing you to set DEBUG directly from the
environment, to slow you down and think before you set this.

ZenSlackChat AS-IS Architecture
-------------------------------

.. image:: docs/zenslackchat-overview.png
    :align: center

XML
~~~~
::
<mxfile host="app.diagrams.net" modified="2023-07-31T10:54:27.888Z" type="device">
  <diagram name="Page-1" id="ho_-8FaknvWiQzevA0_S">
    <mxGraphModel dx="941" dy="509" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="abcUdvEtyeqS7iwiEpK1-16" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-12">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="1045" y="1040" as="targetPoint" />
          </mxGeometry>
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-23" value="Y" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" vertex="1" connectable="0" parent="abcUdvEtyeqS7iwiEpK1-16">
          <mxGeometry x="-0.0637" relative="1" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-87" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-12" target="abcUdvEtyeqS7iwiEpK1-38">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="910" y="909" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-89" value="N" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" vertex="1" connectable="0" parent="abcUdvEtyeqS7iwiEpK1-87">
          <mxGeometry x="-0.65" relative="1" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-12" value="Is this message part&lt;br&gt;of a thread?" style="rhombus;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="830" y="995.47" width="160" height="89.06" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-64" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-13" target="abcUdvEtyeqS7iwiEpK1-58">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-83" value="Y" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" vertex="1" connectable="0" parent="abcUdvEtyeqS7iwiEpK1-64">
          <mxGeometry x="0.1012" y="4" relative="1" as="geometry">
            <mxPoint as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-76" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-13" target="abcUdvEtyeqS7iwiEpK1-39">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-84" value="N" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" vertex="1" connectable="0" parent="abcUdvEtyeqS7iwiEpK1-76">
          <mxGeometry x="-0.1747" y="5" relative="1" as="geometry">
            <mxPoint y="1" as="offset" />
          </mxGeometry>
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-13" value="Is the issue&amp;nbsp;&lt;br&gt;resolved?" style="rhombus;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="1045" y="995.47" width="140" height="90" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-35" value="" style="shape=image;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;image=https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Zendesk_logo.svg/2560px-Zendesk_logo.svg.png;" vertex="1" parent="1">
          <mxGeometry x="1093.97" y="844.23" width="42.05" height="30" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-70" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-38" target="abcUdvEtyeqS7iwiEpK1-53">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-38" value="Create new Zendesk&lt;br&gt;ticket" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="1055" y="879.23" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-39" value="Add comment to Zendesk ticket" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="1258.98" y="1010" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-52" value="" style="shape=image;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;image=https://logos-world.net/wp-content/uploads/2020/10/Slack-Logo.png;" vertex="1" parent="1">
          <mxGeometry x="1280" y="846" width="71.11" height="40" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-53" value="Send ticket&lt;br&gt;created confirmation" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="1258.98" y="879.23" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-74" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-58" target="abcUdvEtyeqS7iwiEpK1-73">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-58" value="Set Zendesk ticket&lt;br&gt;status to &quot;closed&quot;" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="1055" y="1142" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-69" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-60" target="abcUdvEtyeqS7iwiEpK1-12">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-60" value="Message received from&amp;nbsp;SRE requests&lt;br&gt;channel" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="640" y="1010.47" width="130" height="60" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-73" value="Send Slack message&lt;br&gt;confirming ticket resolution" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="1055" y="1255" width="120" height="60" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-80" value="" style="shape=image;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;image=https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Zendesk_logo.svg/2560px-Zendesk_logo.svg.png;" vertex="1" parent="1">
          <mxGeometry x="1297.95" y="975" width="42.05" height="30" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-81" value="" style="shape=image;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;image=https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Zendesk_logo.svg/2560px-Zendesk_logo.svg.png;" vertex="1" parent="1">
          <mxGeometry x="1007" y="1157" width="42.05" height="30" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-82" value="" style="shape=image;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=0;image=https://logos-world.net/wp-content/uploads/2020/10/Slack-Logo.png;" vertex="1" parent="1">
          <mxGeometry x="978.89" y="1265" width="71.11" height="40" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-85" value="Thread id and chat id are stored as a look up" style="text;strokeColor=none;align=center;fillColor=none;html=1;verticalAlign=middle;whiteSpace=wrap;rounded=0;" vertex="1" parent="1">
          <mxGeometry x="855" y="1100" width="110" height="30" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-93" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;entryX=0;entryY=0.5;entryDx=0;entryDy=0;" edge="1" parent="1" source="abcUdvEtyeqS7iwiEpK1-91" target="abcUdvEtyeqS7iwiEpK1-60">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="abcUdvEtyeqS7iwiEpK1-91" value="Person needing&lt;br&gt;support" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;" vertex="1" parent="1">
          <mxGeometry x="546" y="1010" width="30" height="60" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>