from datetime import timedelta
from unittest.mock import patch

from allianceauth.tests.auth_utils import AuthUtils
from django_webtest import WebTest

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from django.test import TestCase
from django.test.utils import override_settings

from . import LoadTestDataMixin, create_test_user
from ..models import DiscordWebhook, NotificationRule, Timer
from ..tasks import send_notifications, send_test_message_to_webhook


class TestUI(LoadTestDataMixin, WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # user 1
        cls.user_1 = create_test_user(cls.character_1)

        # user 2
        cls.user_2 = create_test_user(cls.character_2)
        AuthUtils.add_permission_to_user_by_name(
            "timerboard2.timer_management", cls.user_2
        )
        cls.user_2 = User.objects.get(pk=cls.user_2.pk)

    def setUp(self) -> None:
        self.timer_1 = Timer.objects.create(
            structure_name="Timer 1",
            date=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
        )
        self.timer_2 = Timer.objects.create(
            structure_name="Timer 2",
            date=now() - timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
        )
        self.timer_3 = Timer.objects.create(
            structure_name="Timer 3",
            date=now() - timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_1,
            eve_solar_system=self.system_enaluri,
            structure_type=self.type_astrahus,
        )

    def test_add_new_timer(self):
        """
        when user has permissions
        then he can create a new timer
        """

        # login
        self.app.set_user(self.user_2)

        # user opens timerboard
        timerboard = self.app.get(reverse("timerboard2:timer_list"))
        self.assertEqual(timerboard.status_code, 200)

        # user clicks on "Add Timer"
        add_timer = timerboard.click(href=reverse("timerboard2:add"))
        self.assertEqual(add_timer.status_code, 200)

        # user enters data and clicks create
        form = add_timer.forms["add-timer-form"]
        form["days_left"] = 1
        form["structure_name"] = "Timer 4"
        form["eve_solar_system_2"].force_value([str(self.system_abune.id)])
        form["structure_type_2"].force_value([str(self.type_astrahus.id)])
        form["days_left"] = 1
        form["hours_left"] = 2
        form["minutes_left"] = 3
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("timerboard2:timer_list"))
        self.assertTrue(Timer.objects.filter(structure_name="Timer 4").exists())

    def test_edit_existing_timer(self):
        """
        when user has permissions
        then he can edit an existing timer
        """

        # login
        self.app.set_user(self.user_2)

        # user opens timerboard
        timerboard = self.app.get(reverse("timerboard2:timer_list"))
        self.assertEqual(timerboard.status_code, 200)

        # user clicks on "Edit Timer" for timer 1
        edit_timer = self.app.get(reverse("timerboard2:edit", args=[self.timer_1.pk]))
        self.assertEqual(edit_timer.status_code, 200)

        # user enters data and clicks create
        form = edit_timer.forms["add-timer-form"]
        form["owner_name"] = "The Boys"
        response = form.submit()
        self.timer_1.refresh_from_db()

        # assert results
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("timerboard2:timer_list"))
        self.assertEqual(self.timer_1.owner_name, "The Boys")

    def test_delete_existing_timer(self):
        """
        when user has permissions
        then he can delete an existing timer
        """

        # login
        self.app.set_user(self.user_2)

        # user opens timerboard
        timerboard = self.app.get(reverse("timerboard2:timer_list"))
        self.assertEqual(timerboard.status_code, 200)

        # user clicks on "Delete Timer" for timer 2
        confirm_page = self.app.get(
            reverse("timerboard2:delete", args=[self.timer_2.pk])
        )
        self.assertEqual(confirm_page.status_code, 200)

        # user enters data and clicks create
        form = confirm_page.forms["confirm-delete-form"]
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("timerboard2:timer_list"))
        self.assertFalse(Timer.objects.filter(pk=self.timer_2.pk).exists())


@override_settings(CELERY_ALWAYS_EAGER=True)
@patch("timerboard2.models.sleep", new=lambda x: x)
@patch("timerboard2.models.dhooks_lite.Webhook.execute")
class TestSendNotifications(LoadTestDataMixin, TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        self.rule_1 = NotificationRule.objects.create(
            minutes=NotificationRule.MINUTES_15
        )
        self.rule_1.webhooks.add(self.webhook)

        self.rule_2 = NotificationRule.objects.create(
            minutes=NotificationRule.MINUTES_30
        )
        self.rule_2.webhooks.add(self.webhook)

    def test_normal(self, mock_execute):
        Timer.objects.create(
            structure_name="Test_1",
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            date=now(),
        )
        Timer.objects.create(
            structure_name="Test_2",
            eve_solar_system=self.system_enaluri,
            structure_type=self.type_astrahus,
            date=now() + timedelta(minutes=5),
        )
        send_notifications.delay()
        self.assertEqual(mock_execute.call_count, 4)


@override_settings(CELERY_ALWAYS_EAGER=True)
@patch("timerboard2.models.sleep", new=lambda x: x)
@patch("timerboard2.tasks.notify")
@patch("timerboard2.models.dhooks_lite.Webhook.execute")
class TestTestMessageToWebhook(LoadTestDataMixin, TestCase):
    def setUp(self) -> None:
        self.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        self.user = AuthUtils.create_user("John Doe")

    def test_without_user(self, mock_execute, mock_notify):
        send_test_message_to_webhook.delay(webhook_pk=self.webhook.pk)
        self.assertEqual(mock_execute.call_count, 1)
        self.assertFalse(mock_notify.called)

    def test_with_user(self, mock_execute, mock_notify):
        send_test_message_to_webhook.delay(
            webhook_pk=self.webhook.pk, user_pk=self.user.pk
        )
        self.assertEqual(mock_execute.call_count, 1)
        self.assertTrue(mock_notify.called)
