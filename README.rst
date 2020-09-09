Zenslackchat 
============

.. contents::

Helpdesk support using a slack chat bot and integration into zendesk.

I use make, docker, python3 and virtualenvwrappers to manage the project.

Spike Investigation
-------------------

Scenario / chat with Matt / Things to work out on SRE-725:

- user types in question on the slack channel (without /<command> ideally).
   - OM: I'm using slack client and subscribing to message events. I get *all* 
     the messages including my own. I then have control over how to react, 
     although its a bit tricky.
- Bot instantly replies in a thread that this got assigned a ticket ID X. Ticket is stored in Zendesk
   - OM: I've got this working as requireds.
- Ticket in zendesk filled in with end user email so that user gets updated on the progress. 
   - OM: I recover the slack message author's email. I then add this as the 
     recipient when creating the ticket. I'll need to see how this works in the
     field.
- Record URL to the conversation on slack
   - OM: |ss| Your can add URL to slack thread as a custom field on zendesk. |se|
      - I can add a custom field. Then you need to find its unique ID. To set
        it you then user the custom_fields: [{'id': <id>, 'value': '...'}]. This
        is a bit unweildy.
      - When you set this in the code, it does populate the text box with the 
        link however it is not clickable. I didn't see a HTML link option as a
        field.
   - OM: A better approach (in my view) I've added the link as the first 
     ticket_comment. This is clickable and opens slack to reveal the message 
     thread.
- SRE on call follows up with the conversation on slack
- Bot replicates the conversation into zendesk ticket
   - OM: I'll need to look into webhooks at least for the zendesk to slack 
     replication. So new comments in zendesk trigger the bot to put them in 
     the slack chat.
- SRE on call closes the ticket by typing “done” or similar within the thread
   - OM: This works now, it could be any string. Maybe done is too vague. 
     Should anyone be able to type "done" to close the issue?
- Can we avoid /<command> actions?
  - OM: yes there is not need for these.
- Ticket assigned to every thread.
  - Webops metrics time open/cycle time.
     - OM: Zendesk does have metrics, have to investigate.
     - OM: Bot could reply with stats in response to query.
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
 - [] Synchronise state changes on a ticket from Zendesk(?).
 - [] ship messages from zendesk to slack
 

Zendesk Webhook
~~~~~~~~~~~~~~~

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


Webhook Development
```````````````````

Sign-up for a free Ngrok.io account. This allows you to have a public 
accessible HTTP endpoint to your local instance for development. Run ngrok
locally as follows::

   ngrok http 12380

This should then give you a URL you can use in the HTTP Target. For example 
http://ed8a1df2e030.ngrok.io. This changes each time its restarted so you will
need to update the HTTP Target when this happens.

Set up the webhook environment variables::

   # set up the ENV variables which are the same as those used by the bot
   export ZENDESK_EMAIL=...
   export ZENDESK_SUBDOMAIN=...
   export ZENDESK_TICKET_URI=...
   export ZENDESK_TOKEN=...
   export SLACK_WORKSPACE_URI=...
   export SLACKBOT_API_TOKEN=...

Now run the webhook using flask as follows. Note the port needs to be the same
as the Ngrok tunnel::

   workon zenslackchat

   # (Python3)
   FLASK_ENV=development FLASK_APP='zenslackchat.service:create_app()' \
      flask run --port 12380


Zenslackchat Bot
~~~~~~~~~~~~~~~~

I've merged what I've done so far into a single approach. I'm going to set up
a demo to show progress and get user feedback end of the week. This will help
decided whether to continue/drop.

set up
``````

For Zendesk integration ou need to enable and generate a token (not oauth):
 - https://support.zendesk.com/hc/en-us/articles/226022787-Generating-a-new-API-token-

The token approach is functional, however its permissons are too broad using 
this method. To get off the ground its fine, but we'll need to move to OAuth
in production. I don't want to do this in a spike.

Zendesk OAuth:
- https://support.zendesk.com/hc/en-us/articles/203663836-Using-OAuth-authentication-with-your-application

Useful Reference docs:

- https://developer.zendesk.com/rest_api/docs/support/tickets#json-format
- https://developer.zendesk.com/rest_api/docs/support/ticket_comments
- Zenpy: http://docs.facetoe.com.au/api_objects.html
- http://docs.facetoe.com.au/zenpy.html

For Slack integration I'm using the Python slackclient library. It has handy
event based systen. You subscribe to a message event and then receive *all*
messages including your own. 

To set up slack you need to do the following. When signed into a workspace 
(correct admin rights?) go to:

- https://my.slack.com/services/new/bot

settings::

    username: gofer
    what this bot does: Run between slack and zendesk

You can then recover the API_TOKEN slackbot needs. I created a zenslackchat 
channel in my workspace. I had to invite the bot before it could be used.


Demo
````

To run the demo bot::

    workon zenslackchat

    # Set up the credentials:
    # zendesk
    export ZENDESK_EMAIL=<user on support site> 
    export ZENDESK_SUBDOMAIN=<support site subdomain>
    export ZENDESK_TICKET_URI=https://<support site>.zendesk.com/agent/tickets
    read -srp "Zendesk Token: " ZENDESK_TOKEN ; export ZENDESK_TOKEN
    # slack
    export SLACK_WORKSPACE_URI=https://<workspace>.slack.com/archives
    read -srp "SLACKBOT_API_TOKEN: " SLACKBOT_API_TOKEN ; export SLACKBOT_API_TOKEN
    
    # Run the bot (Python3)
    python zenslackchat/main.py


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

Release
-------

**Not set up yet**

If all the tests pass then you can do a release to the AWS ECR repository by
doing::

    # rerun the tests to be sure:
    make test docker_build docker_test docker_release

You will need to have logged-in to AWS and recovered the credentials to allow
docker to push.


.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>