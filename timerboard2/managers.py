from django.db import models


class TimerManager(models.Manager):
    def send_notifications(self):
        pass
