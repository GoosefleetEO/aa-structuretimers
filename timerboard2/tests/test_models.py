from datetime import timedelta
import json
from unittest.mock import patch

import dhooks_lite

from django.core.cache import cache
from django.test import TestCase
from django.utils.timezone import now

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo


from . import LoadTestDataMixin
from ..models import DiscordWebhook, NotificationRule, Timer
from ..utils import JSONDateTimeDecoder, NoSocketsTestCase


MODULE_PATH = "timerboard2.models"


class TestTimer(LoadTestDataMixin, TestCase):
    def test_str(self):
        timer = Timer(
            structure_name="Test",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )
        expected = "Armor timer for Abune (Raitaru)"
        self.assertEqual(str(timer), expected)

    def test_structure_display_name(self):
        timer = Timer(
            structure_name="Test",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )
        expected = "Abune (Raitaru)"
        self.assertEqual(timer.structure_display_name, expected)

    def test_label_type_for_timer_type(self):
        timer = Timer(date=now())
        self.assertEqual(timer.label_type_for_timer_type(), "default")

        timer.timer_type = timer.TYPE_ARMOR
        self.assertEqual(timer.label_type_for_timer_type(), "danger")

        timer.timer_type = timer.TYPE_HULL
        self.assertEqual(timer.label_type_for_timer_type(), "danger")

    def test_label_type_for_objective(self):
        timer = Timer(date=now())
        self.assertEqual(timer.label_type_for_objective(), "default")

        timer.objective = Timer.OBJECTIVE_HOSTILE
        self.assertEqual(timer.label_type_for_objective(), "danger")

        timer.objective = Timer.OBJECTIVE_FRIENDLY
        self.assertEqual(timer.label_type_for_objective(), "primary")


@patch(MODULE_PATH + ".DiscordWebhook.send_message")
class TestTimerSendNotification(LoadTestDataMixin, TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )

    def test_normal(self, mock_send_message):
        timer = Timer.objects.create(
            structure_name="Test",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )

        timer.send_notification(self.webhook)

        self.assertEqual(mock_send_message.call_count, 1)

    def test_with_ping_type(self, mock_send_message):
        timer = Timer.objects.create(
            structure_name="Test",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )

        timer.send_notification(self.webhook, "@here")

        self.assertEqual(mock_send_message.call_count, 1)
        _, kwargs = mock_send_message.call_args
        self.assertIn("@here", kwargs["content"])


@patch(MODULE_PATH + ".NotificationRule._import_send_messages_for_webhook")
@patch(MODULE_PATH + ".Timer.send_notification")
class TestNotificationRuleProcessTimers(LoadTestDataMixin, TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        self.timer = Timer.objects.create(
            structure_name="Test",
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )
        self.rule = NotificationRule.objects.create(minutes=NotificationRule.MINUTES_15)
        self.rule.webhooks.add(self.webhook)

    def test_normal(
        self, mock_send_notification, mock_import_send_messages_for_webhook
    ):
        result = self.rule.process_timers()

        self.assertIn(self.timer.pk, result)
        self.assertEqual(mock_send_notification.call_count, 1)
        _, kwargs = mock_send_notification.call_args
        self.assertEqual(kwargs["webhook"], self.webhook)

        self.assertEqual(
            mock_import_send_messages_for_webhook.return_value.delay.call_count, 1
        )
        _, kwargs = mock_import_send_messages_for_webhook.return_value.delay.call_args
        self.assertEqual(kwargs["webhook_pk"], self.webhook.pk)

    def test_minutes(
        self, mock_send_notification, mock_import_send_messages_for_webhook
    ):
        self.timer.date = now() + timedelta(hours=1)
        self.timer.save()

        self.assertFalse(self.rule.process_timers())

    def test_require_timer_types(
        self, mock_send_notification, mock_import_send_messages_for_webhook
    ):
        # do not process if it does not match
        self.rule.require_timer_types = [Timer.TYPE_ARMOR]
        self.rule.save()
        self.assertFalse(self.rule.process_timers())

        # process if it does match
        self.timer.timer_type = Timer.TYPE_ARMOR
        self.timer.save()
        self.assertIn(self.timer.pk, self.rule.process_timers())

    def test_require_objectives(
        self, mock_send_notification, mock_import_send_messages_for_webhook
    ):
        # do not process if it does not match
        self.rule.require_objectives = [Timer.OBJECTIVE_HOSTILE]
        self.rule.save()
        self.assertFalse(self.rule.process_timers())

        # process if it does match
        self.timer.objective = Timer.OBJECTIVE_HOSTILE
        self.timer.save()
        self.assertIn(self.timer.pk, self.rule.process_timers())

    def test_require_corporations(
        self, mock_send_notification, mock_import_send_messages_for_webhook
    ):
        # do not process if it does not match
        self.rule.require_corporations.add(
            EveCorporationInfo.objects.get(corporation_id=2001)
        )
        self.assertFalse(self.rule.process_timers())

        # process if it does match
        self.timer.eve_corporation = EveCorporationInfo.objects.get(corporation_id=2001)
        self.timer.save()
        self.assertIn(self.timer.pk, self.rule.process_timers())

    def test_require_alliances(
        self, mock_send_notification, mock_import_send_messages_for_webhook
    ):
        # do not process if it does not match
        self.rule.require_alliances.add(EveAllianceInfo.objects.get(alliance_id=3001))
        self.assertFalse(self.rule.process_timers())

        # process if it does match
        self.timer.eve_alliance = EveAllianceInfo.objects.get(alliance_id=3001)
        self.timer.save()
        self.assertIn(self.timer.pk, self.rule.process_timers())


class TestDiscordWebhook(LoadTestDataMixin, TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )

    def test_str(self):
        self.assertEqual(str(self.webhook), "Dummy")

    def test_repr(self):
        self.assertEqual(
            repr(self.webhook), f"DiscordWebhook(id={self.webhook.id}, name='Dummy')"
        )

    def test_queue_features(self):
        cache.clear()
        self.assertEqual(self.webhook.queue_size(), 0)
        self.webhook.send_message(content="Dummy message")
        self.assertEqual(self.webhook.queue_size(), 1)
        self.webhook.clear_queue()
        self.assertEqual(self.webhook.queue_size(), 0)

    def test_send_message_normal(self):
        cache.clear()
        embed = dhooks_lite.Embed(description="my_description")
        self.assertEqual(
            self.webhook.send_message(
                content="my_content",
                username="my_username",
                avatar_url="my_avatar_url",
                embeds=[embed],
            ),
            1,
        )
        message = json.loads(
            self.webhook._main_queue.dequeue(), cls=JSONDateTimeDecoder
        )
        expected = {
            "content": "my_content",
            "embeds": [{"description": "my_description", "type": "rich"}],
            "username": "my_username",
            "avatar_url": "my_avatar_url",
        }
        self.assertDictEqual(message, expected)

    def test_send_message_empty(self):
        cache.clear()
        with self.assertRaises(ValueError):
            self.webhook.send_message()


@patch(MODULE_PATH + ".sleep", new=lambda x: x)
@patch(MODULE_PATH + ".DiscordWebhook.send_message_to_webhook")
class TestDiscordWebhookSendQueuedMessages(TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        self.webhook.clear_queue()

    def test_one_message(self, mock_send_message_to_webhook):
        """
        when one mesage in queue 
        then send it and returns 1
        """
        mock_send_message_to_webhook.return_value = True
        self.webhook.send_message("dummy")

        result = self.webhook.send_queued_messages()

        self.assertEqual(result, 1)
        self.assertTrue(mock_send_message_to_webhook.called)
        self.assertEqual(self.webhook.queue_size(), 0)

    def test_three_message(self, mock_send_message_to_webhook):
        """
        when three mesages in queue 
        then sends them and returns 3
        """
        mock_send_message_to_webhook.return_value = True
        self.webhook.send_message("dummy-1")
        self.webhook.send_message("dummy-2")
        self.webhook.send_message("dummy-3")

        result = self.webhook.send_queued_messages()

        self.assertEqual(result, 3)
        self.assertEqual(mock_send_message_to_webhook.call_count, 3)
        self.assertEqual(self.webhook.queue_size(), 0)

    def test_no_messages(self, mock_send_message_to_webhook):
        """
        when no message in queue 
        then do nothing and return 0
        """
        mock_send_message_to_webhook.return_value = True
        result = self.webhook.send_queued_messages()

        self.assertEqual(result, 0)
        self.assertFalse(mock_send_message_to_webhook.called)
        self.assertEqual(self.webhook.queue_size(), 0)

    def test_failed_message(self, mock_send_message_to_webhook):
        """
        given one message in queue 
        when sending fails 
        then re-queues message and return 0
        """
        mock_send_message_to_webhook.return_value = False
        self.webhook.send_message("dummy")

        result = self.webhook.send_queued_messages()

        self.assertEqual(result, 0)
        self.assertTrue(mock_send_message_to_webhook.called)
        self.assertEqual(self.webhook.queue_size(), 1)


@patch(MODULE_PATH + ".dhooks_lite.Webhook.execute")
@patch(MODULE_PATH + ".logger")
class TestDiscordWebhookSendMessageToWebhook(NoSocketsTestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )

    def test_send_normal(self, mock_logger, mock_execute):
        """
            when sending of message successful
            return True
        """
        mock_execute.return_value = dhooks_lite.WebhookResponse(
            headers=dict(), status_code=200
        )
        message = {
            "content": "my_content",
            "embeds": [{"description": "my_description", "type": "rich"}],
            "username": "my_username",
            "avatar_url": "my_avatar_url",
        }

        result = self.webhook.send_message_to_webhook(message)

        self.assertTrue(result)
        self.assertTrue(mock_execute.called)
        _, kwargs = mock_execute.call_args
        self.assertDictEqual(
            kwargs,
            {
                "content": "my_content",
                "embeds": [
                    dhooks_lite.Embed.from_dict(
                        {"description": "my_description", "type": "rich"}
                    )
                ],
                "username": "my_username",
                "avatar_url": "my_avatar_url",
                "wait_for_response": True,
            },
        )
        self.assertFalse(mock_logger.warning.called)

    def test_send_failed(self, mock_logger, mock_execute):
        """
            when sending of message failed
            then log warning and return False
        """
        mock_execute.return_value = dhooks_lite.WebhookResponse(
            headers=dict(), status_code=440
        )
        message = {
            "content": "my_content",
            "embeds": [{"description": "my_description", "type": "rich"}],
            "username": "my_username",
            "avatar_url": "my_avatar_url",
        }

        result = self.webhook.send_message_to_webhook(message)

        self.assertFalse(result)
        self.assertTrue(mock_execute.called)
        self.assertTrue(mock_logger.warning.called)
