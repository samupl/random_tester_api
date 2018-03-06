import random

from django.conf import settings
from django.db import transaction
from slackclient import SlackClient

from apps.api.random_tester.models import SlackUser, SlackUserStack


def sync_slack_users():
    sc = SlackClient(settings.SLACK_OAUTH_TOKEN)
    response = sc.api_call('users.list')
    for member in response['members']:
        profile = member['profile']
        slack_id = member['id']
        user_name = member['name']
        real_name = member.get('real_name', '')
        avatar_url = (
            profile.get('image_48') or
            profile.get('image_32') or
            profile.get('image_24')
        )
        slack_user = SlackUser.objects.get_or_create(
            slack_id=slack_id
        )[0]
        slack_user.user_name = user_name
        slack_user.real_name = real_name
        slack_user.avatar_url = avatar_url
        slack_user.save()


def get_random_tester_for_channel(channel_id, members):
    with transaction.atomic():
        channel_stacks = SlackUserStack.objects.filter(channel_id=channel_id)
        default_query = {
            'slack_id__in': members,
            'is_tester': True,
        }
        testers = SlackUser.objects.filter(**default_query).exclude(
            slack_id__in={
                stack.slack_user.slack_id for stack in channel_stacks
            }
        )

        if not testers.exists():
            channel_stacks.delete()
            testers = SlackUser.objects.filter(**default_query)

        tester = random.choice(testers)
        SlackUserStack.objects.create(channel_id=channel_id, slack_user=tester)
    return tester
