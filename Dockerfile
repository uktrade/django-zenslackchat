FROM python:3.8 as build
WORKDIR /app

ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . /app

ENV DJANGO_SETTINGS_MODULE webapp.settings

# DB access
ENV DB_HOST 127.0.0.1
ENV DB_PORT 5432
ENV DB_NAME service
ENV DB_USER service
ENV DB_PASSWORD service

# Slack App OAuth credentials
ENV SLACK_CLIENT_ID <some id>
ENV SLACK_CLIENT_SECRET <secret>
ENV SLACK_VERIFICATION_TOKEN <verification token>
ENV SLACK_SIGN_SECRET <sign secret>
ENV SLACK_BOT_USER_TOKEN <bot user token>
ENV SLACK_WORKSPACE_URI  <https://...slack.com/archives>

# Zendesk
ENV ZENDESK_EMAIL <someone-at-uktrade@example.com>
ENV ZENDESK_SUBDOMAIN <staging-uktrade>
ENV ZENDESK_TOKEN <zendesk token>
ENV ZENDESK_TICKET_URI https://staging-uktrade.zendesk.com/agent/tickets

FROM build as prod
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "webapp.wsgi"]`

FROM build as test
ADD requirements-test.txt .
RUN pip install -r requirements-test.txt
CMD ["pytest", "-s"]
