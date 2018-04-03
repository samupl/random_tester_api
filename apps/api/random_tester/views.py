import random
from functools import wraps

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
from slackclient import SlackClient
import threading

from apps.api.random_tester.tools import get_random_tester_for_channel
from apps.api.random_tester.waiting_funnies import WAITING_FUNNIES


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
    return {
        'response_type': 'ephemeral',
        'text': msg
    }


def pick_random_tester(channel_id, ticket_id, response_url):
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
    ticket_assignee_url = (
        f'{settings.JIRA_BASE_URL}/{ticket_id}/assignee'
    )
    resp = requests.get(
        ticket_url,
        auth=auth,
    )
    if resp.status_code != 200:
        requests.post(
            response_url,
            json=user_error('Ticket not found')
        )
        return

    ticket_response = resp.json()
    ticket_status = ticket_response['fields']['status']['name']
    if ticket_status != settings.EXPECTED_TICKET_STATUS:
        return requests.post(
            response_url,
            json=user_error(
                f'Ticket status it not "{settings.EXPECTED_TICKET_STATUS}". '
                f'Current status: "{ticket_status}"'
            ),
        )

    if ticket_response['fields']['assignee']:
        return requests.post(
            response_url,
            json=user_error('Somebody is already working on this ticket, silly.'),
        )

    members = response['members']
    selected_tester = get_random_tester_for_channel(
        channel_id=channel_id,
        members=members
    )

    requests.put(
        ticket_assignee_url,
        json={
            'name': selected_tester.user_name
        },
        auth=auth,
    )
    return requests.post(
        response_url,
        json={
            'text': f'Ticket *{ticket_id}* will be tested by...',
            'response_type': 'in_channel',
            'attachments': [
                {
                    'image_url': selected_tester.avatar_url,
                    'pretext': f'<@{selected_tester.slack_id}>',
                    'color': '#3da2e2',
                    'footer': random_motivational_line(),
                },
                # {'text': f'<@{selected_tester.slack_id}>'}
            ],
        }
    )


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

    t = threading.Thread(target=pick_random_tester, kwargs={
        'channel_id': channel_id,
        'ticket_id': ticket_id,
        'response_url': request.POST['response_url']
    })
    t.daemon = True
    t.start()

    return JsonResponse({
        "response_type": "ephemeral",
        'text': (
            f'Please wait.\n{random.choice(WAITING_FUNNIES)}'
        )
    })


def random_motivational_line():
    return random.choice([
        'Go get it!',
        'Have fun!',
        'Go get it tiger!',
        'Have at it!',
        'You can do it!'
    ])
