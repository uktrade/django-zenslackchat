Hello World 
===========

.. contents::

I use make, docker, docker-compose, python3 and virtualenvwrappers to manage 
the project.

Development
-----------

To set up the code for development you can do::

    mkvirtualenv --clear -p python3 helloworld
    make install

To run the service locally in the dev environment do::

    # activate the env
    workon helloworld

    # Start postgresql
    make up

    # Create/migrate the DB schema ready for use:
    make migrate

    # run the webapp
    make run

If you go to https://localhost:8000/ you will see the message "Database is empty!"
as no "hello content" has been set. This can be done quickly using the REST 
API. For example::

    $ curl -H 'Content-Type: application/json' \
        -d '{"value": "Hello World"}' \
        http://localhost:8000/v1/hellocontent/
    {"created":"2020-07-20T16:46:08.729931Z","value":"Hello World"}
    $

If you now look at https://localhost:8000/ you will see "Hello World". 
Alternatively You can create a superuser to use the admin interface using::

    python manage.py createsuperuser

Then go to http://localhost:8000/admin and then navigate to the "Hello contents" 
admin section and add an entry. 

You can add multiple hello content entries, however only the latest created 
entry is shown.


Testing
-------

With docker compose running postgres in one window, you can run the tests as
follows::

    # activate the env
    workon helloworld

    # Run basic model and view tests
    make test

Release
-------

If all the tests pass then you can do a release to the AWS ECR repository by
doing::

    # rerun the tests to be sure:
    make test docker_build docker_release

You will need to have logged-in to AWS and recovered the credentials to allow
docker to push. The helloworld_terraform README shows how to do this.
