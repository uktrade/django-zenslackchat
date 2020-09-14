export NAMESPACE=zenslackchat

.DEFAULT_GOAL := all

.PHONY: all run migrate remove release reinstall test up ps down 

all:
	echo "Please choose a make target to run."

install:
	pip install -r requirements.txt

test_install:
	pip install -r requirements-test.txt

clean:
	rm -rf dist/ build/
	rm -f README.pdf
	find . -iname '*.pyc' -exec rm {} \; -print

run:
	python manage.py runserver

migrate:
	python manage.py migrate

remove:
	cf delete -r -f ${NAMESPACE}

release:
	# deploy to the organisation/space previous configured with cf target
	cf push

reinstall: remove release

rlogs:
	cf logs ${NAMESPACE}

up:
	docker-compose --project-name ${NAMESPACE} up --remove-orphans

ps:
	docker-compose --project-name ${NAMESPACE} ps

down:
	docker-compose --project-name ${NAMESPACE} logs -t
	docker-compose --project-name ${NAMESPACE} down --remove-orphans

lint:
	flake8 --ignore=E501 webapp
	flake8 --ignore=E501 zenslackchat

test:
	pytest
