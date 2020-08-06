from datetime import timedelta
from unittest.mock import patch
from io import StringIO

from django.core.management import call_command
from django.utils.timezone import now

from allianceauth.timerboard.models import Timer as AuthTimer

from . import LoadTestDataMixin, create_test_user
from ..models import Timer
from ..utils import NoSocketsTestCase

PACKAGE_PATH = "timerboard2.management.commands"


@patch("timerboard2.models.TIMERBOARD2_NOTIFICATIONS_ENABLED", False)
@patch(PACKAGE_PATH + ".structuretimers_migrate_timers.get_input")
class TestMigirateTimers(LoadTestDataMixin, NoSocketsTestCase):
    def setUp(self) -> None:
        self.user = create_test_user(self.character_1)

    def test_normal(self, mock_get_input):
        mock_get_input.return_value = "Y"
        Timer.objects.all().delete()
        auth_timer = AuthTimer.objects.create(
            details="Armor timer",
            system="Abune",
            planet_moon="Near Heydieles gate",
            structure="Astrahus",
            objective="Friendly",
            eve_time=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corp=self.corporation_1,
            user=self.user,
        )
        out = StringIO()
        call_command("structuretimers_migrate_timers", stdout=out)

        new_timer = Timer.objects.first()
        self.assertEqual(new_timer.eve_solar_system, self.system_abune)
        self.assertEqual(new_timer.structure_type, self.type_astrahus)
        self.assertEqual(new_timer.timer_type, Timer.TYPE_ARMOR)
        self.assertEqual(new_timer.details_notes, "Armor timer")
        self.assertEqual(new_timer.objective, Timer.OBJECTIVE_FRIENDLY)
        self.assertEqual(new_timer.date, auth_timer.eve_time)
        self.assertEqual(new_timer.eve_character, self.character_1)
        self.assertEqual(new_timer.eve_corporation, self.corporation_1)
        self.assertEqual(new_timer.user, auth_timer.user)
