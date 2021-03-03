from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat.models import PagerDutyApp
from zenslackchat.models import ZenSlackChat
from zenslackchat.slack_api import message_url
from zenslackchat.zendesk_api import zendesk_ticket_url


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

    list_display = (
        'chat_id', 'channel_id', 'ticket_id_url', 'slack_chat_url', 'active',
        'opened', 'closed'
    )

    list_filter = ('active', 'opened', 'closed')

    search_fields = ('chat_id', 'ticket_id')

    def slack_chat_url(self, obj):
        chat_url = message_url(
            settings.SLACK_WORKSPACE_URI, obj.channel_id, obj.chat_id
        )
        sid = chat_url.split('/')[-1]
        return format_html(f'<a href="{chat_url}">{sid}</a>')

    def ticket_id_url(self, obj):
        url = zendesk_ticket_url(
            settings.ZENDESK_TICKET_URI, obj.ticket_id
        )
        return format_html(f'<a href="{url}">{obj.ticket_id}</a>')
