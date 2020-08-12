Zenslackchat 
============

.. contents::

Helpdesk support using a slack chat bot and integration into zendesk.

I use make, docker, docker-compose, python3 and virtualenvwrappers to manage 
the project.

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
