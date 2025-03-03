#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

export DATABASE_URL=postgresql://service:service@localhost:5432/service
export REDIS_URL=redis://localhost:6379/
export WEBAPP_SECRET_KEY=random-secret-key-18912789489589725608243789
export SLACK_CLIENT_ID=
export SLACK_CLIENT_SECRET=
export SLACK_SIGN_SECRET=
export SLACK_VERIFICATION_TOKEN=
export SLACK_WORKSPACE_URI=
export PAAS_FQDN=*
export SRE_SUPPORT_CHANNEL=
export SENTRY_DSN=
export ZENDESK_CLIENT_IDENTIFIER=zenslackchatstaging
export ZENDESK_CLIENT_SECRET=
export ZENDESK_SUBDOMAIN=
export ZENDESK_TICKET_URI=
export ZENDESK_REDIRECT_URI=
export ZENDESK_WEBHOOK_TOKEN=
export ZENDESK_USER_ID=
export ZENDESK_GROUP_ID=
export ZENDESK_AGENT_EMAIL=
export PAGERDUTY_CLIENT_IDENTIFIER=
export PAGERDUTY_CLIENT_SECRET=
export PAGERDUTY_REDIRECT_URI=
export PAGERDUTY_ESCALATION_POLICY_ID=
export CSRF_TRUSTED_ORIGINS=zenslackchat.app

# Add commands below to run inside the container after all the other buildpacks have been applied
echo "Running collectstatic"
python manage.py collectstatic --noinput
