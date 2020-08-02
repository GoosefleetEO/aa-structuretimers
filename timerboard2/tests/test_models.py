from django.test import TestCase
from django.utils.timezone import now

from eveuniverse.models import EveSolarSystem, EveType

from ..models import Timer
from .testdata.load_eveuniverse import load_eveuniverse


class TestTimer(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_eveuniverse()
        cls.type_astrahus = EveType.objects.get(id=35832)
        cls.type_raitaru = EveType.objects.get(id=35825)
        cls.system_abune = EveSolarSystem.objects.get(id=30004984)
        cls.system_enaluri = EveSolarSystem.objects.get(id=30045339)

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
