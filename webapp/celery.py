import os

from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')

app = Celery('django-zenslackchat')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.timezone = 'Europe/London'


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up the daily report.
    """
    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        # 07:30 monday -> friday
        crontab(hour=7, minute=30, day_of_week='1-5'),
        run_daily_summary,
    )


@app.task(ignore_result=True)
def run_daily_summary():
    """Generate and send the daily summary report to slack.
    """
    from webapp import settings
    from zenslackchat.models import SlackApp
    from zenslackchat.models import ZenSlackChat

    channel_id = settings.SRE_SUPPORT_CHANNEL
    workspace_uri = settings.SLACK_WORKSPACE_URI

    report_data = ZenSlackChat.daily_summary(workspace_uri)
    text = ZenSlackChat.daily_report(report_data)

    client = SlackApp.client()
    client.chat_postMessage(channel=channel_id, text=text)    