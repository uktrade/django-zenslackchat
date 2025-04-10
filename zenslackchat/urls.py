# -*- coding: utf-8 -*-
from django.contrib.auth import views as auth_views
from django.urls import path

from . import eventsview, views, zendesk_webhooks

urlpatterns = [
    path("", views.index, name="index"),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("slack/oauth/", views.slack_oauth, name="slack_oauth"),
    path("slack/events/", eventsview.Events.as_view(), name="slack_events"),
    path("zendesk/oauth/", views.zendesk_oauth, name="zendesk_oauth"),
    path(
        "zendesk/webhook/",
        zendesk_webhooks.CommentsWebHook.as_view(),
        name="zenslackchat_comments",
    ),
    path(
        "zendesk/email/webhook/",
        zendesk_webhooks.EmailWebHook.as_view(),
        name="zenslackchat_emails",
    ),
    # path('pagerduty/oauth/', views.pagerduty_oauth, name='pagerduty_oauth'),
    path("trigger/report/daily", views.trigger_daily_report, name="daily_report"),
    path("confluence/start_oauth/", views.start_oauth, name="start_oauth"),
    path("callback/", views.callback, name="callback"),
    path("confluence/fetch_page/", views.fetch_page, name="fetch_page"),
    path("confluence/logout/", views.confluence_logout, name="fetch_page"),
]
