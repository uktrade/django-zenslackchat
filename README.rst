Zenslackchat 
============

.. contents::

Helpdesk support using a slack chat bot and integration into zendesk.

I use make, docker, docker-compose, python3 and virtualenvwrappers to manage 
the project.

Spike Investigation
-------------------

Scenario / chat with Matt / Things to work out on SRE-725:

- user types in question on the slack channel (without /<command> ideally).
- Bot instantly replies in a thread that this got assigned a ticket ID X. Ticket is stored in Zendesk
   - OM: creating a ticket I've figured out. I've also learned if the same text is put in again it will result in a zendesk error on create. I'll need to manage around this.
- Ticket in zendesk filled in with end user email so that user gets updated on the progress. 
   - OM: If I can recover this from slack they can be added as a CC to the issue.
- Record URL to the conversation on slack
   - OM: Your can add URL to slack thread as a custom field on zendesk.
- SRE on call follows up with the conversation on slack
- Bot replicates the conversation into zendesk ticket
- SRE on call closes the ticket by typing “done” or similar within the thread
- Can we avoid /<command> actions?
- Ticket assigned to every thread.
  - Webops metrics time open/cycle time.
     - OM: Zendesk does have metrics, have to investigate.
     - OM: Bot could reply with stats in response to query.
  - Primary/Secondary people on support added to ticket.
     - If you had a way to query some API for who is "on call", this could be added automatically as Ticket assignees.

Todo
~~~~

Zendesk API investigation.
 - [X] |ss| Get access credentials for API access to a Zendesk |se|
 - [X] |ss| Choose a python Zendesk |se| 
 - [x] |ss| Create a zendesk ticket and investigate structure |se| 

Slackbot investigation.
 - [] Slackbot reading
 - [] Skeletal slackbot and slack integration.
 - [] Can bot respond to a user without using a slack command?
 - [] Can bot respond in a thread?


Zendesk integration
~~~~~~~~~~~~~~~~~~~

You need to enable and generate a token (not oauth):
 - https://support.zendesk.com/hc/en-us/articles/226022787-Generating-a-new-API-token-

Current experiment::

    # Set up the credentials:
    export ZENDESK_EMAIL=<user on support site> 
    export ZENDESK_SUBDOMAIN=<support site subdomain>
    read -srp "Zendesk Token: " ZENDESK_TOKEN ; export ZENDESK_TOKEN

    workon zenslackchat
    
    # from a checkout of zenslackchat/ (python3)
    python zenslackchat/zendesk_demo.py

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


Slack Bot
~~~~~~~~~

I'm going to see if I can use this open source python slackbot library:

- https://github.com/lins05/slackbot.

I'm currently experimenting using my own slack group so I can get an idea of what supporting this end-to-end will be like.

Set up
``````

When signed into a workspace (correct admin rights?) go to:

- https://my.slack.com/services/new/bot

settings::

    username: gofer
    what this bot does: Run between slack and zendesk

You can then recover the API_TOKEN slackbot needs.

Current experiment::

    # Set up the credentials:
    read -srp "SLACKBOT_API_TOKEN: " SLACKBOT_API_TOKEN ; export SLACKBOT_API_TOKEN

    workon zenslackchat
    
    # from a checkout of zenslackchat/ (python3)
    python zenslackchat/goferbot.py

I created a zenslackchat channel in my workspace. I had to invite the bot into before it will respond.

On slack you can then see if the bot is running by looking at the status of the @gofer user. Alternatively you can say hello::    

    oisin: @gofer hello
    gofer: @oisin: hello sender!


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

If all the tests pass then you can do a release to the AWS ECR repository by
doing::

    # rerun the tests to be sure:
    make test docker_build docker_release

You will need to have logged-in to AWS and recovered the credentials to allow
docker to push.


.. |ss| raw:: html

   <strike>

.. |se| raw:: html

   </strike>