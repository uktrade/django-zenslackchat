FROM python:3.8 as build
WORKDIR /app

ADD requirements.txt .
RUN pip install -r requirements.txt --no-cache-di
COPY . /app
RUN python setup.py develop

# Need to be set, these are only example values:
ENV ZENDESK_EMAIL user@example.com
ENV ZENDESK_SUBDOMAIN zendeskhelp.example.com
ENV ZENDESK_TICKET_URI https://zendeskhelp.example.com/agent/tickets
ENV SLACK_WORKSPACE_URI https://workspace.example.com/archives
ENV SLACKBOT_API_TOKEN this-token-to-use

FROM build as prod
EXPOSE 8000
CMD ["python", "zenslackchat/main.py"]

FROM build as test
ADD requirements-test.txt .
RUN pip install -r requirements-test.txt
CMD ["pytest", '-s', '--cov=zenslackchat']
