from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth_views

from . import views
from . import eventsview
from . import zendesk_webhook_view


urlpatterns = [
    path('', views.index, name='index'),

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('slack/oauth/', views.slack_oauth, name='slack_oauth'),
    path('slack/events/', eventsview.Events.as_view(), name='slack_events'),

    path('zendesk/oauth/', views.zendesk_oauth, name='zendesk_oauth'),
    path(
        'zendesk/webhook/', 
        zendesk_webhook_view.WebHook.as_view(), 
        name='slack_events'
    ),
]