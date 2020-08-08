from datetime import datetime, timedelta
import json
from unittest.mock import patch

import dhooks_lite

from django.core.cache import cache
from django.test import TestCase
from django.utils.timezone import now

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from . import LoadTestDataMixin
from ..models import DiscordWebhook, NotificationRule, Timer, models
from ..utils import JSONDateTimeDecoder, NoSocketsTestCase


MODULE_PATH = "structuretimers.models"


class TestTimer(LoadTestDataMixin, TestCase):
    def test_str(self):
        timer = Timer(
            structure_name="Test",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=datetime(2020, 8, 6, 13, 25),
        )
        expected = 'Armor timer for Raitaru "Test" in Abune @ 2020-08-06 13:25'
        self.assertEqual(str(timer), expected)

    def test_structure_display_name_1(self):
        timer = Timer(
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=datetime(2020, 8, 6, 13, 25),
        )
        expected = "Raitaru in Abune"
        self.assertEqual(timer.structure_display_name, expected)

    def test_structure_display_name_2(self):
        timer = Timer(
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            location_details="P5-M3",
            date=datetime(2020, 8, 6, 13, 25),
        )
        expected = "Raitaru in Abune near P5-M3"
        self.assertEqual(timer.structure_display_name, expected)

    def test_structure_display_name_3(self):
        timer = Timer(
            structure_name="Big Boy",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=datetime(2020, 8, 6, 13, 25),
        )
        expected = 'Raitaru "Big Boy" in Abune'
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
        timer = Timer(
            structure_name="Test",
            timer_type=Timer.TYPE_ARMOR,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )
        timer.send_notification(self.webhook)

        self.assertEqual(mock_send_message.call_count, 1)

    def test_with_ping_type(self, mock_send_message):
        timer = Timer(
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


@patch(MODULE_PATH + ".TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
class TestTimerQuerySet(LoadTestDataMixin, TestCase):
    @patch(MODULE_PATH + ".TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
    def setUp(self) -> None:
        self.timer_1 = Timer(
            structure_name="Timer 1",
            date=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            timer_type=Timer.TYPE_ARMOR,
            objective=Timer.OBJECTIVE_FRIENDLY,
        )
        self.timer_1.save()
        self.timer_2 = Timer(
            structure_name="Timer 2",
            date=now() - timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            timer_type=Timer.TYPE_HULL,
            objective=Timer.OBJECTIVE_FRIENDLY,
        )
        self.timer_2.save()
        self.timer_qs = Timer.objects.all()
        self.webhook = DiscordWebhook.objects.create(name="Dummy", url="my-url")

    def test_conforms_with_notification_rule_1(self):
        """
        given two timers in qs
        when one timer conforms with notification rule
        then qs contains only conforming timer
        """
        rule = NotificationRule.objects.create(
            minutes=NotificationRule.MINUTES_10,
            require_timer_types=[Timer.TYPE_ARMOR],
            webhook=self.webhook,
        )
        new_qs = self.timer_qs.conforms_with_notification_rule(rule)
        self.assertIsInstance(new_qs, models.QuerySet)
        self.assertSetEqual(set(new_qs.values_list("pk", flat=True)), {self.timer_1.pk})

    def test_conforms_with_notification_rule_2(self):
        """
        given two timers in qs
        when no timer conforms with notification rule
        then qs is empty
        """
        rule = NotificationRule.objects.create(
            minutes=NotificationRule.MINUTES_10, webhook=self.webhook,
        )
        rule.require_corporations.add(self.corporation_3)
        new_qs = self.timer_qs.conforms_with_notification_rule(rule)
        self.assertIsInstance(new_qs, models.QuerySet)
        self.assertSetEqual(set(new_qs.values_list("pk", flat=True)), set())

    def test_conforms_with_notification_rule_3(self):
        """
        given two timers in qs
        when all timer conforms with notification rule
        then qs contains all timers
        """
        rule = NotificationRule.objects.create(
            minutes=NotificationRule.MINUTES_10,
            require_objectives=[Timer.OBJECTIVE_FRIENDLY],
            webhook=self.webhook,
        )
        new_qs = self.timer_qs.conforms_with_notification_rule(rule)
        self.assertIsInstance(new_qs, models.QuerySet)
        self.assertSetEqual(
            set(new_qs.values_list("pk", flat=True)), {self.timer_1.pk, self.timer_2.pk}
        )


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


@patch(MODULE_PATH + ".TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
class TestNotificationRuleIsMatchingTimer(LoadTestDataMixin, TestCase):
    @patch(MODULE_PATH + ".TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(name="Dummy", url="my-url")
        self.timer = Timer.objects.create(
            structure_name="Test",
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )
        self.rule = NotificationRule.objects.create(
            minutes=NotificationRule.MINUTES_15, webhook=self.webhook
        )

    def test_require_timer_types(self):
        # do not process if it does not match
        self.rule.require_timer_types = [Timer.TYPE_ARMOR]
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.timer_type = Timer.TYPE_ARMOR
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_timer_types(self):
        # process if it does match
        self.rule.exclude_timer_types = [Timer.TYPE_ARMOR]
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.timer_type = Timer.TYPE_ARMOR
        self.assertFalse(self.rule.is_matching_timer(self.timer))

    def test_require_objectives(self):
        # do not process if it does not match
        self.rule.require_objectives = [Timer.OBJECTIVE_HOSTILE]
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.objective = Timer.OBJECTIVE_HOSTILE
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_objectives(self):
        # process if it does match
        self.rule.exclude_objectives = [Timer.OBJECTIVE_HOSTILE]
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.objective = Timer.OBJECTIVE_HOSTILE
        self.assertFalse(self.rule.is_matching_timer(self.timer))

    def test_require_corporations(self):
        # do not process if it does not match
        self.rule.require_corporations.add(
            EveCorporationInfo.objects.get(corporation_id=2001)
        )
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.eve_corporation = EveCorporationInfo.objects.get(corporation_id=2001)
        self.timer.save()
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_corporations(self):
        # process if it does match
        self.rule.exclude_corporations.add(
            EveCorporationInfo.objects.get(corporation_id=2001)
        )
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.eve_corporation = EveCorporationInfo.objects.get(corporation_id=2001)
        self.timer.save()
        self.assertFalse(self.rule.is_matching_timer(self.timer))

    def test_require_alliances(self):
        # do not process if it does not match
        self.rule.require_alliances.add(EveAllianceInfo.objects.get(alliance_id=3001))
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.eve_alliance = EveAllianceInfo.objects.get(alliance_id=3001)
        self.timer.save()
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_alliances(self):
        # process if it does match
        self.rule.exclude_alliances.add(EveAllianceInfo.objects.get(alliance_id=3001))
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.eve_alliance = EveAllianceInfo.objects.get(alliance_id=3001)
        self.timer.save()
        self.assertFalse(self.rule.is_matching_timer(self.timer))

    def test_require_visibility(self):
        # do not process if it does not match
        self.rule.require_visibility = [Timer.VISIBILITY_CORPORATION]
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.visibility = Timer.VISIBILITY_CORPORATION
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_visibility(self):
        # process if it does match
        self.rule.exclude_visibility = [Timer.VISIBILITY_CORPORATION]
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.visibility = Timer.VISIBILITY_CORPORATION
        self.assertFalse(self.rule.is_matching_timer(self.timer))

    def test_require_important(self):
        # do not process if it does not match
        self.rule.is_important = NotificationRule.CLAUSE_REQUIRED
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.is_important = True
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_important(self):
        # process if it does match
        self.rule.is_important = NotificationRule.CLAUSE_EXCLUDED
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.is_important = True
        self.assertFalse(self.rule.is_matching_timer(self.timer))

    def test_require_opsec(self):
        # do not process if it does not match
        self.rule.is_opsec = NotificationRule.CLAUSE_REQUIRED
        self.assertFalse(self.rule.is_matching_timer(self.timer))

        # process if it does match
        self.timer.is_opsec = True
        self.assertTrue(self.rule.is_matching_timer(self.timer))

    def test_exclude_opsec(self):
        # process if it does match
        self.rule.is_opsec = NotificationRule.CLAUSE_EXCLUDED
        self.assertTrue(self.rule.is_matching_timer(self.timer))

        # do not process if it does not match
        self.timer.is_opsec = True
        self.assertFalse(self.rule.is_matching_timer(self.timer))


@patch(MODULE_PATH + ".TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
class TestNotificationRuleQuerySet(LoadTestDataMixin, TestCase):
    @patch(MODULE_PATH + ".TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(name="Dummy", url="my-url")
        self.rule_1 = NotificationRule.objects.create(
            minutes=10, require_timer_types=[Timer.TYPE_ARMOR], webhook=self.webhook
        )
        self.rule_2 = NotificationRule.objects.create(
            minutes=15,
            require_objectives=[Timer.OBJECTIVE_FRIENDLY],
            webhook=self.webhook,
        )
        self.rule_qs = NotificationRule.objects.all()

    def test_conforms_with_timer_1(self):
        """
        given two rules in qs
        when one rule conforms with timer
        then qs contains only conforming rule
        """
        timer = Timer(
            structure_name="Test Timer",
            date=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            timer_type=Timer.TYPE_ARMOR,
            objective=Timer.OBJECTIVE_HOSTILE,
        )
        timer.save()
        new_qs = self.rule_qs.conforms_with_timer(timer)
        self.assertIsInstance(new_qs, models.QuerySet)
        self.assertSetEqual(set(new_qs.values_list("pk", flat=True)), {self.rule_1.pk})

    def test_conforms_with_timer_2(self):
        """
        given two rules in qs
        when no rule conforms with timer
        then qs is empty
        """
        timer = Timer(
            structure_name="Test Timer",
            date=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            timer_type=Timer.TYPE_HULL,
            objective=Timer.OBJECTIVE_HOSTILE,
        )
        timer.save()
        new_qs = self.rule_qs.conforms_with_timer(timer)
        self.assertIsInstance(new_qs, models.QuerySet)
        self.assertSetEqual(set(new_qs.values_list("pk", flat=True)), set())

    def test_conforms_with_timer_3(self):
        """
        given two rules in qs
        when one rule conforms with timer
        then qs contains only conforming rule
        """
        timer = Timer(
            structure_name="Test Timer",
            date=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            timer_type=Timer.TYPE_ARMOR,
            objective=Timer.OBJECTIVE_FRIENDLY,
        )
        timer.save()
        new_qs = self.rule_qs.conforms_with_timer(timer)
        self.assertIsInstance(new_qs, models.QuerySet)
        self.assertSetEqual(
            set(new_qs.values_list("pk", flat=True)), {self.rule_1.pk, self.rule_2.pk}
        )
