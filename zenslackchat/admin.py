from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html

from zenslackchat.models import SlackApp
from zenslackchat.models import ZendeskApp
from zenslackchat.models import PagerDutyApp
from zenslackchat.models import ZenSlackChat
from zenslackchat.slack_api import message_url
from zenslackchat.slack_api import url_to_chat_id
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
        'chat_id', 'channel_id', 'ticket_url', 'chat_url', 'active', 'opened',
        'closed'
    )

    search_fields = ('chat_id', 'ticket_id')

    list_filter = ('active', 'opened', 'closed')

    actions = ('mark_resolved',)

    def chat_url(self, obj):
        """Provide a link to the slack chat."""
        url = message_url(
            settings.SLACK_WORKSPACE_URI, obj.channel_id, obj.chat_id
        )
        sid = url.split('/')[-1]
        return format_html(f'<a href="{url}">{sid}</a>')

    def ticket_url(self, obj):
        """Provide a link to the issue on Zendesk."""
        url = zendesk_ticket_url(
            settings.ZENDESK_TICKET_URI, obj.ticket_id
        )
        return format_html(f'<a href="{url}">{obj.ticket_id}</a>')

    def get_search_results(self, request, queryset, search_term):
        """Support Slack chat url to chat_id conversion and searching."""
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        if queryset.count() == 0:
            chat_id = url_to_chat_id(search_term)
            queryset |= self.model.objects.filter(chat_id=chat_id)

        return queryset, use_distinct

    def mark_resolved(modeladmin, request, queryset):
        """Allow the admin to close issue.

        This only resolves the issue in our database, stopping the bot from
        monitoring it further. Zendesk will not be notified and no notice will
        be sent on Slack.

        It allows the admin to remove an issue if something went wrong. For
        example zendesk was down and the issue was partially created.

        """
        for obj in queryset:
            ZenSlackChat.resolve(obj.channel_id, obj.chat_id)

    mark_resolved.short_description = "Remove an issue by marking it resolved."
