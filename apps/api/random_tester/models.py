from django.db import models


class SlackUser(models.Model):
    slack_id = models.CharField(unique=True, primary_key=True, max_length=32)
    user_name = models.CharField(max_length=512)
    real_name = models.CharField(max_length=512)
    avatar_url = models.CharField(max_length=1024, null=True)
    is_tester = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_tester', '-user_name']

    def __str__(self):
        return f'{self.slack_id}: {self.user_name}'


class SlackUserStack(models.Model):
    slack_user = models.ForeignKey(SlackUser, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=32)
