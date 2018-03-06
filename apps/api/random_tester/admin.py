from django.contrib import admin
from django.utils.html import format_html

from apps.api.random_tester.models import SlackUser


@admin.register(SlackUser)
class SlackUserAdmin(admin.ModelAdmin):
    list_display = [
        'slack_id', 'avatar', 'user_name', 'real_name', 'is_tester'
    ]
    search_fields = ['user_name', 'real_name']

    def avatar(self, obj):
        if not obj.avatar_url:
            return '-'
        return format_html(f'<img src="{obj.avatar_url}" style="max-width: 32px;">')
