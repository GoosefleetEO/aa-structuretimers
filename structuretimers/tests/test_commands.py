from datetime import timedelta
from unittest.mock import patch
from io import StringIO

from django.core.management import call_command
from django.utils.timezone import now

from allianceauth.timerboard.models import Timer as AuthTimer

from . import LoadTestDataMixin, create_test_user
from ..models import Timer
from ..utils import NoSocketsTestCase, app_labels

PACKAGE_PATH = "structuretimers.management.commands"


@patch("structuretimers.models.TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
@patch(PACKAGE_PATH + ".structuretimers_migrate_timers.get_input")
class TestMigirateTimers(LoadTestDataMixin, NoSocketsTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if "timerboard" not in app_labels():
            raise KeyboardInterrupt(
                "App `timerboard` is not installed, which is required for this test"
            )

    def setUp(self) -> None:
        self.out = StringIO()
        self.user = create_test_user(self.character_1)
        self.auth_timer = AuthTimer.objects.create(
            system="Abune",
            planet_moon="Near Heydieles gate",
            structure="Astrahus",
            eve_time=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corp=self.corporation_1,
            user=self.user,
        )
        Timer.objects.all().delete()

    def test_full_armor_friendly(self, mock_get_input):
        mock_get_input.return_value = "Y"
        self.auth_timer.details = "Armor timer"
        self.auth_timer.objective = "Friendly"
        self.auth_timer.save()

        call_command("structuretimers_migrate_timers", stdout=self.out)

        new_timer = Timer.objects.first()
        self.assertEqual(new_timer.eve_solar_system, self.system_abune)
        self.assertEqual(new_timer.structure_type, self.type_astrahus)
        self.assertEqual(new_timer.timer_type, Timer.TYPE_ARMOR)
        self.assertEqual(new_timer.details_notes, "Armor timer")
        self.assertEqual(new_timer.objective, Timer.OBJECTIVE_FRIENDLY)
        self.assertEqual(new_timer.date, self.auth_timer.eve_time)
        self.assertEqual(new_timer.eve_character, self.character_1)
        self.assertEqual(new_timer.eve_corporation, self.corporation_1)
        self.assertEqual(new_timer.user, self.auth_timer.user)

    def test_hull_hostile(self, mock_get_input):
        mock_get_input.return_value = "Y"
        self.auth_timer.details = "Hull timer"
        self.auth_timer.objective = "Hostile"
        self.auth_timer.save()

        call_command("structuretimers_migrate_timers", stdout=self.out)

        new_timer = Timer.objects.first()
        self.assertEqual(new_timer.timer_type, Timer.TYPE_HULL)
        self.assertEqual(new_timer.objective, Timer.OBJECTIVE_HOSTILE)

    def test_anchoring(self, mock_get_input):
        mock_get_input.return_value = "Y"
        self.auth_timer.details = "Anchor timer"
        self.auth_timer.objective = "Neutral"
        self.auth_timer.save()

        call_command("structuretimers_migrate_timers", stdout=self.out)

        new_timer = Timer.objects.first()
        self.assertEqual(new_timer.timer_type, Timer.TYPE_ANCHORING)
        self.assertEqual(new_timer.objective, Timer.OBJECTIVE_NEUTRAL)

    """
    def test_moon_mining(self, mock_get_input):
        mock_get_input.return_value = "Y"
        self.auth_timer.structure = "Moon Mining Cycle"
        self.auth_timer.save()

        call_command("structuretimers_migrate_timers", stdout=self.out)

        new_timer = Timer.objects.first()
        self.assertEqual(new_timer.timer_type, Timer.TYPE_MOONMINING)
        self.assertEqual(new_timer.structure_type, Timer.OBJECTIVE_NEUTRAL)
    """
