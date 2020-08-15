from unittest.mock import patch

from django_webtest import WebTest

from django.contrib.auth.models import User
from django.urls import reverse

from . import LoadTestDataMixin
from ..models import DiscordWebhook, NotificationRule, Timer


@patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
class TestNotificationRuleChangeList(LoadTestDataMixin, WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        cls.user = User.objects.create_superuser(
            "Bruce Wayne", "bruce@example.com", "password"
        )

    @patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
    def setUp(self) -> None:
        NotificationRule.objects.create(
            trigger=NotificationRule.TRIGGER_SCHEDULED_TIME_REACHED,
            scheduled_time=NotificationRule.MINUTES_10,
            webhook=self.webhook,
        )
        NotificationRule.objects.create(
            trigger=NotificationRule.TRIGGER_SCHEDULED_TIME_REACHED,
            scheduled_time=NotificationRule.MINUTES_10,
            require_timer_types=[Timer.TYPE_ARMOR],
            webhook=self.webhook,
        )
        rule = NotificationRule.objects.create(
            trigger=NotificationRule.TRIGGER_SCHEDULED_TIME_REACHED,
            scheduled_time=NotificationRule.MINUTES_10,
            webhook=self.webhook,
        )
        rule.require_corporations.add(self.corporation_1)
        NotificationRule.objects.create(
            trigger=NotificationRule.TRIGGER_SCHEDULED_TIME_REACHED,
            scheduled_time=NotificationRule.MINUTES_10,
            is_important=NotificationRule.CLAUSE_EXCLUDED,
            webhook=self.webhook,
        )

    def test_can_open_page_normally(self):
        # login
        self.app.set_user(self.user)

        # user tries to add new notification rule
        add_page = self.app.get(
            reverse("admin:structuretimers_notificationrule_changelist")
        )
        self.assertEqual(add_page.status_code, 200)


@patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
class TestNotificationRuleValidations(LoadTestDataMixin, WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.webhook = DiscordWebhook.objects.create(
            name="Dummy", url="http://www.example.com"
        )
        cls.user = User.objects.create_superuser(
            "Bruce Wayne", "bruce@example.com", "password"
        )
        cls.url_add = reverse("admin:structuretimers_notificationrule_add")
        cls.url_changelist = reverse(
            "admin:structuretimers_notificationrule_changelist"
        )

    def setUp(self) -> None:
        NotificationRule.objects.all().delete()

    def _open_page(self) -> object:
        # login
        self.app.set_user(self.user)

        # user tries to add new notification rule
        add_page = self.app.get(self.url_add)
        self.assertEqual(add_page.status_code, 200)
        form = add_page.form
        form["trigger"] = NotificationRule.TRIGGER_SCHEDULED_TIME_REACHED
        form["scheduled_time"] = NotificationRule.MINUTES_10
        form["webhook"] = self.webhook.pk
        return form

    def test_no_errors(self):
        form = self._open_page()
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_changelist)
        self.assertEqual(NotificationRule.objects.count(), 1)

    def test_can_not_have_same_options_timer_types(self):
        form = self._open_page()
        form["require_timer_types"] = [Timer.TYPE_ANCHORING, Timer.TYPE_HULL]
        form["exclude_timer_types"] = [Timer.TYPE_ANCHORING, Timer.TYPE_ARMOR]
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please correct the error below", response.text)
        self.assertEqual(NotificationRule.objects.count(), 0)

    def test_can_not_have_same_options_objectives(self):
        form = self._open_page()
        form["require_objectives"] = [Timer.OBJECTIVE_FRIENDLY, Timer.OBJECTIVE_HOSTILE]
        form["exclude_objectives"] = [Timer.OBJECTIVE_FRIENDLY, Timer.OBJECTIVE_NEUTRAL]
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please correct the error below", response.text)
        self.assertEqual(NotificationRule.objects.count(), 0)

    def test_can_not_have_same_options_visibility(self):
        form = self._open_page()
        form["require_visibility"] = [Timer.VISIBILITY_CORPORATION]
        form["exclude_visibility"] = [Timer.VISIBILITY_CORPORATION]
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please correct the error below", response.text)
        self.assertEqual(NotificationRule.objects.count(), 0)

    def test_can_not_have_same_options_corporations(self):
        form = self._open_page()
        form["require_corporations"] = [self.corporation_1.pk, self.corporation_3.pk]
        form["exclude_corporations"] = [self.corporation_1.pk]
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please correct the error below", response.text)
        self.assertEqual(NotificationRule.objects.count(), 0)

    def test_can_not_have_same_options_alliances(self):
        form = self._open_page()
        form["require_alliances"] = [self.alliance_1.pk, self.alliance_3.pk]
        form["exclude_alliances"] = [self.alliance_1.pk]
        response = form.submit()

        # assert results
        self.assertEqual(response.status_code, 200)
        self.assertIn("Please correct the error below", response.text)
        self.assertEqual(NotificationRule.objects.count(), 0)
