GIT_COMMIT?=$(shell git rev-parse HEAD)
BRANCH_NAME?=$(shell git rev-parse --abbrev-ref HEAD)
BRANCH_TAG=$(subst /,_,$(BRANCH_NAME))

DOCKER_REPO=someplaceonaws.dkr.ecr.eu-west-2.amazonaws.com
DOCKER_NAME=zenslackchat_service

DOCKER_IMAGE=${DOCKER_NAME}:${GIT_COMMIT}
DOCKER_BRANCH_IMAGE=${DOCKER_NAME}:${BRANCH_NAME}-latest

.DEFAULT_GOAL := all
.PHONY: all install clean run test docker_build docker_test up down ps docs lint

# Need to be set in the environment, these are only example values:
export ZENDESK_EMAIL?=user@example.com
export ZENDESK_SUBDOMAIN?=zendeskhelp.example.com
export ZENDESK_TICKET_URI?=https://zendeskhelp.example.com/agent/tickets
export SLACK_WORKSPACE_URI?=https://workspace.example.com/archives
export SLACKBOT_API_TOKEN?=this-token-to-use

all:
	echo "Please choose a make target to run."

install:
	pip install -r requirements-test.txt
	python setup.py develop

clean:
	rm -rf dist/ build/
	rm -f README.pdf
	find . -iname '*.pyc' -exec rm {} \; -print

docker_build: clean
	docker build \
		-t ${DOCKER_IMAGE} \
		-t ${DOCKER_BRANCH_IMAGE} \
		-t ${DOCKER_REPO}/${DOCKER_IMAGE} \
		-t ${DOCKER_REPO}/${DOCKER_BRANCH_IMAGE} \
		--target prod .
	docker build \
		-t ${DOCKER_IMAGE}-test \
		-t ${DOCKER_BRANCH_IMAGE}-test \
		-t ${DOCKER_REPO}/${DOCKER_IMAGE}-test \
		-t ${DOCKER_REPO}/${DOCKER_BRANCH_IMAGE}-test \
		--target test .

run:
	python zenslackchat/main.py

docker_test:
	docker run \
		--rm \
		${DOCKER_IMAGE}-test \
		bash -c "make test"

docker_release:
	echo "NOOP"
	#docker push ${DOCKER_REPO}/${DOCKER_IMAGE}
	#docker push ${DOCKER_REPO}/${DOCKER_BRANCH_IMAGE}

lint:
	flake8 --ignore=E501 zenslackchat

test:
	pytest -s --cov=zenslackchat

