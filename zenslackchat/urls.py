from django.urls import path

from . import views
from . import eventsview
from . import zendesk_webhook_view


urlpatterns = [
    path('', views.index, name='index'),
    path('slack/oauth/', views.slack_oauth, name='slack_oauth'),
    path('slack/events/', eventsview.Events.as_view(), name='slack_events'),
    path(
        'zendesk/webhook/', 
        zendesk_webhook_view.WebHook.as_view(), 
        name='slack_events'
    ),
]