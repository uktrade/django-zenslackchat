from django.contrib import admin


from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat.models import PagerDutyApp
from zenslackchat.models import ZenSlackChat


@admin.register(SlackApp)
class SlackAppAdmin(admin.ModelAdmin):
    """Manage the stored Slack OAuth client credentials.
    """
    date_hierarchy = 'created_at'


@admin.register(ZendeskApp)
class ZendeskAppAdmin(admin.ModelAdmin):
    """Manage the stored Zendesk OAuth client credentials
    """
    date_hierarchy = 'created_at'


@admin.register(PagerDutyApp)
class PagerDutyAppAdmin(admin.ModelAdmin):
    """Manage the stored PagerDuty OAuth client credentials
    """
    date_hierarchy = 'created_at'


@admin.register(ZenSlackChat)
class ZenSlackChatAdmin(admin.ModelAdmin):
    """Manage the stored support resquests
    """
    date_hierarchy = 'opened'

