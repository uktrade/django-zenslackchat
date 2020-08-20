GIT_COMMIT?=$(shell git rev-parse HEAD)
BRANCH_NAME?=$(shell git rev-parse --abbrev-ref HEAD)
BRANCH_TAG=$(subst /,_,$(BRANCH_NAME))

DOCKER_REPO=someplaceonaws.dkr.ecr.eu-west-2.amazonaws.com
DOCKER_NAME=zenslackchat_service

DOCKER_IMAGE=${DOCKER_NAME}:${GIT_COMMIT}
DOCKER_BRANCH_IMAGE=${DOCKER_NAME}:${BRANCH_NAME}-latest

.DEFAULT_GOAL := all
.PHONY: all install clean run test docker_build docker_test up down ps docs lint

export DB_HOST?=127.0.0.1
export DB_NAME=service
export DB_USER=service
export DB_PASS=service
export DB_PORT?=5432
export POSTGRES_HOST?=127.0.0.1
export POSTGRES_NAME=service
export POSTGRES_USER=service
export POSTGRES_PASS=service
export POSTGRES_PORT?=5432

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
	python -c "import time; print('NOOP'); time.sleep(500)"

up:
	docker-compose --project-name ${DOCKER_NAME} up --remove-orphans

ps:
	docker-compose --project-name ${DOCKER_NAME} ps

down:
	docker-compose --project-name ${DOCKER_NAME} logs -t
	docker-compose --project-name ${DOCKER_NAME} down --remove-orphans

docker_test:
	docker run \
		--rm \
		--network=${DOCKER_NAME}_default \
		-e DB_HOST=postgres \
		-e DB_USER=${DB_USER} \
		-e DB_NAME=${DB_NAME} \
		-e DB_PASS=${DB_PASS} \
		-e DB_PORT=${DB_PORT} \
		${DOCKER_IMAGE}-test \
		bash -c "make test"

docker_release:
	docker push ${DOCKER_REPO}/${DOCKER_IMAGE}
	docker push ${DOCKER_REPO}/${DOCKER_BRANCH_IMAGE}

lint:
	flake8 --ignore=E501 zenslackchat

test:
	pytest -s --cov=zenslackchat

