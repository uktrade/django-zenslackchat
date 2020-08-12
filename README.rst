Zenslackchat 
============

.. contents::

Helpdesk support using a slack chat bot and integration into zendesk.

I use make, docker, docker-compose, python3 and virtualenvwrappers to manage 
the project.


Project Objectives
------------------

Jira ticket Epic for project https://uktrade.atlassian.net/jira/software/projects/SRE/boards/167?selectedIssue=SRE-725&text=slack

The scenario:
 - user types in question on the slack channel.
 - Bot instantly replies in a thread that this got assigned a ticket ID X. Ticket is stored in Zendesk
 - Ticket in zendesk is filled in with end user email so that user gets updated on the progress. Also record URL to the conversation on slack
 - SRE on call follows up with the conversation on slack
 - Bot replicates the conversation into zendesk ticket
 - SRE on call closes the ticket by typing “done” or similar within the thread


Spike to investigate this
~~~~~~~~~~~~~~~~~~~~~~~~~

Zendesk API investigation.

[] Get access credentials for API access to a Zendesk
[] Choose a python Zendesk
[] Create a zendesk ticket and investigate structure
[] Update the existing 

Slackbot investigation.

[] Slackbot reading
[] Skeletal slackbot and slack integration.
[] Can bot respond to a user without using a slack command?
[] Can bot respond in a thread?


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
