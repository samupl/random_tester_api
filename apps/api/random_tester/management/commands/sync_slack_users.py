from django.core.management import BaseCommand

from apps.api.random_tester.tools import sync_slack_users


class Command(BaseCommand):
    def handle(self, *args, **options):
        sync_slack_users()
