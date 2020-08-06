from datetime import timedelta
from unittest.mock import patch, Mock

from django.test import TestCase
from django.utils.timezone import now

from . import LoadTestDataMixin
from ..models import DiscordWebhook, NotificationRule, ScheduledNotification, Timer
from ..tasks import (
    send_messages_for_webhook,
    schedule_notifications_for_timer,
    scheduled_notifications_for_rule,
    send_scheduled_notification,
)
from ..utils import generate_invalid_pk

MODULE_PATH = "structuretimers.tasks"


class TestCaseBase(LoadTestDataMixin, TestCase):
    @patch("structuretimers.models.TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        self.rule = NotificationRule(minutes=NotificationRule.MINUTES_15)
        self.rule.save()
        self.rule.webhooks.add(self.webhook)
        self.timer = Timer(
            structure_name="Test_1",
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now() + timedelta(minutes=30),
        )
        self.timer.save()


@patch(MODULE_PATH + ".DiscordWebhook.send_queued_messages")
@patch(MODULE_PATH + ".logger")
class TestSendMessagesForWebhook(TestCaseBase):
    def test_normal(self, mock_logger, mock_send_queued_messages):
        send_messages_for_webhook(self.webhook.pk)
        self.assertEqual(mock_send_queued_messages.call_count, 1)
        self.assertEqual(mock_logger.info.call_count, 2)
        self.assertEqual(mock_logger.error.call_count, 0)

    def test_invalid_pk(self, mock_logger, mock_send_queued_messages):
        send_messages_for_webhook(generate_invalid_pk(DiscordWebhook))
        self.assertEqual(mock_send_queued_messages.call_count, 0)
        self.assertEqual(mock_logger.info.call_count, 0)
        self.assertEqual(mock_logger.error.call_count, 1)

    def test_disabled_webhook(self, mock_logger, mock_send_queued_messages):
        self.webhook.is_enabled = False
        self.webhook.save()

        send_messages_for_webhook(self.webhook.pk)
        self.assertEqual(mock_send_queued_messages.call_count, 0)
        self.assertEqual(mock_logger.info.call_count, 1)
        self.assertEqual(mock_logger.error.call_count, 0)


@patch(MODULE_PATH + ".send_scheduled_notification")
class TestScheduleNotificationForTimer(TestCaseBase):
    def test_normal(self, mock_send_notification):
        """
        given no notifications scheduled
        when called for timer with matching notification rule
        then schedules new notification
        """
        mock_send_notification.apply_async.return_value.task_id = "my_task_id"

        schedule_notifications_for_timer(self.timer.pk)

        self.assertTrue(mock_send_notification.apply_async.called)
        self.assertTrue(
            ScheduledNotification.objects.filter(
                timer=self.timer, notification_rule=self.rule
            )
        )

    def test_remove_old_notifications(self, mock_send_notification):
        """
        given existing notification
        when called for timer with matching notification rule and changed date
        then deletes existing notification and schedules new notification
        """
        mock_send_notification.apply_async.return_value.task_id = "my_task_id"
        notification_old = ScheduledNotification.objects.create(
            timer=self.timer,
            notification_rule=self.rule,
            timer_date=self.timer.date + timedelta(minutes=5),
            notification_date=self.timer.date - timedelta(minutes=5),
            celery_task_id="99",
        )

        schedule_notifications_for_timer(self.timer.pk)

        self.assertTrue(mock_send_notification.apply_async.called)
        self.assertTrue(
            ScheduledNotification.objects.filter(
                timer=self.timer, notification_rule=self.rule
            )
        )
        self.assertFalse(
            ScheduledNotification.objects.filter(pk=notification_old.pk).exists()
        )


@patch(MODULE_PATH + ".send_scheduled_notification")
class TestScheduleNotificationForRule(TestCaseBase):
    def test_normal(self, mock_send_notification):
        """
        given no notifications scheduled
        when called for notification rule with matching timer
        then schedules new notification
        """
        mock_send_notification.apply_async.return_value.task_id = "my_task_id"

        scheduled_notifications_for_rule(self.rule.pk)

        self.assertTrue(mock_send_notification.apply_async.called)
        self.assertTrue(
            ScheduledNotification.objects.filter(
                timer=self.timer, notification_rule=self.rule
            )
        )

    def test_remove_old_notifications(self, mock_send_notification):
        """
        given existing notification
        when called for notification rule with matching timer
        then deletes existing notification and schedules new notification
        """
        mock_send_notification.apply_async.return_value.task_id = "my_task_id"
        notification_old = ScheduledNotification.objects.create(
            timer=self.timer,
            notification_rule=self.rule,
            timer_date=self.timer.date + timedelta(minutes=5),
            notification_date=self.timer.date - timedelta(minutes=5),
            celery_task_id="99",
        )

        scheduled_notifications_for_rule(self.rule.pk)

        self.assertTrue(mock_send_notification.apply_async.called)
        self.assertTrue(
            ScheduledNotification.objects.filter(
                timer=self.timer, notification_rule=self.rule
            )
        )
        self.assertFalse(
            ScheduledNotification.objects.filter(pk=notification_old.pk).exists()
        )


@patch("structuretimers.models.TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
@patch(MODULE_PATH + ".send_messages_for_webhook")
class TestSendScheduledNotification(TestCaseBase):
    def test_normal(self, mock_send_messages_for_webhook):
        """
        when this notification is correctly scheduled
        then send the notification
        """
        scheduled_notification = ScheduledNotification.objects.create(
            timer=self.timer,
            notification_rule=self.rule,
            celery_task_id="my-id-123",
            timer_date=now() + timedelta(hours=1),
            notification_date=now() + timedelta(minutes=30),
        )
        mock_task = Mock(**{"request.id": "my-id-123"})
        send_scheduled_notification_inner = (
            send_scheduled_notification.__wrapped__.__func__
        )
        send_scheduled_notification_inner(
            mock_task, scheduled_notification_pk=scheduled_notification.pk
        )
        self.assertTrue(mock_send_messages_for_webhook.apply_async.called)

    def test_revoked_notification(self, mock_send_messages_for_webhook):
        """
        when this is not the right task instance
        then discard this notification
        """
        scheduled_notification = ScheduledNotification.objects.create(
            timer=self.timer,
            notification_rule=self.rule,
            celery_task_id="my-id-123",
            timer_date=now() + timedelta(hours=1),
            notification_date=now() + timedelta(minutes=30),
        )
        mock_task = Mock(**{"request.id": "my-id-456"})
        send_scheduled_notification_inner = (
            send_scheduled_notification.__wrapped__.__func__
        )
        send_scheduled_notification_inner(
            mock_task, scheduled_notification_pk=scheduled_notification.pk
        )
        self.assertFalse(mock_send_messages_for_webhook.apply_async.called)

    def test_rule_disabled(self, mock_send_messages_for_webhook):
        """
        when the notification rule for this scheduled notification is disabled
        then discard notification
        """
        self.rule.is_enabled = False
        self.rule.save()
        scheduled_notification = ScheduledNotification.objects.create(
            timer=self.timer,
            notification_rule=self.rule,
            celery_task_id="my-id-123",
            timer_date=now() + timedelta(hours=1),
            notification_date=now() + timedelta(minutes=30),
        )
        mock_task = Mock(**{"request.id": "my-id-123"})
        send_scheduled_notification_inner = (
            send_scheduled_notification.__wrapped__.__func__
        )
        send_scheduled_notification_inner(
            mock_task, scheduled_notification_pk=scheduled_notification.pk
        )
        self.assertFalse(mock_send_messages_for_webhook.apply_async.called)
