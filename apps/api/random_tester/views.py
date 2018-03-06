from functools import wraps

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
from slackclient import SlackClient

from apps.api.random_tester.tools import get_random_tester_for_channel


def slack_token_required(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        request = args[0]
        token = request.POST.get('token')
        if token != settings.SLACK_VERIFICATION_TOKEN:
            raise PermissionDenied()
        return func(*args, **kwargs)
    return wrapped


def user_error(msg):
    return JsonResponse({
        'response_type': 'ephemeral',
        'text': msg
    })


@csrf_exempt
@slack_token_required
def random_tester(request):
    ticket_id = request.POST.get('text')
    channel_id = request.POST['channel_id']
    if not ticket_id:
        return JsonResponse({
            "response_type": "ephemeral",
            'text': (
                'You need to provide ticket number'
            )
        })

    sc = SlackClient(settings.SLACK_OAUTH_TOKEN)

    response = sc.api_call(
        'conversations.members',
        channel=channel_id,
    )
    if not response['ok'] and response['error'] == 'channel_not_found':
        return user_error(
            f'Could not read channel members. '
            f'Please invite {settings.SLACK_BOT_NAME} to the channel.'
        )

    auth = HTTPBasicAuth(
        settings.JIRA_USER,
        settings.JIRA_PASSWORD,
    )
    ticket_url = f'{settings.JIRA_BASE_URL}/{ticket_id}'
    print(ticket_url)
    resp = requests.get(
        ticket_url,
        auth=auth,
    )
    if resp.status_code != 200:
        return user_error('Ticket not found')

    ticket_response = resp.json()
    ticket_status = ticket_response['fields']['status']['name']
    if ticket_status != settings.EXPECTED_TICKET_STATUS:
        return user_error(
            f'Ticket status it not "{settings.EXPECTED_TICKET_STATUS}". '
            f'Current status: "{ticket_status}"'
        )

    if ticket_response['fields']['assignee']:
        return user_error('Somebody is already working on this ticket, silly.')

    members = response['members']
    selected_tester = get_random_tester_for_channel(
        channel_id=channel_id,
        members=members
    )
    return JsonResponse({
        'text': f'Ticket *{ticket_id}* will be tested by...',
        'response_type': 'in_channel',
        'attachments': [
            {'image_url': selected_tester.avatar_url},
            {'text': f'<@{selected_tester.slack_id}>'}
        ],
    })
