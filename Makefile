export NAMESPACE=zenslackchat

# default set up to run with docker compose started DB:
export DATABASE_URL?=postgresql://service:service@localhost:5432/service

.DEFAULT_GOAL := all

.PHONY: all collect run migrate remove release reinstall test up ps down 

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

collect:
	python manage.py collectstatic --noinput

run: collect
	python manage.py runserver

migrate:
	python manage.py migrate

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
	pytest -s --ds=webapp.settings --cov=zenslackchat --cov=webapp
