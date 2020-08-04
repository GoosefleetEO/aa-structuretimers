from unittest.mock import patch

from django.test import TestCase
from django.utils.timezone import now

from . import LoadTestDataMixin
from ..models import DiscordWebhook, NotificationRule, Timer
from ..tasks import send_messages_for_webhook
from ..utils import generate_invalid_pk

MODULE_PATH = "timerboard2.tasks"


class TestCaseBase(LoadTestDataMixin, TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        self.rule = NotificationRule.objects.create(minutes=NotificationRule.MINUTES_15)
        self.rule.webhooks.add(self.webhook)
        self.timer = Timer.objects.create(
            structure_name="Test_1",
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )


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
