from django.test import TestCase
from django.utils.timezone import now

from ..models import Timer
from .testdata.load_eveuniverse import load_eveuniverse


class TestTimer(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        load_eveuniverse()

    def test_str(self):
        timer = Timer(
            details="Test",
            timer_type=Timer.TYPE_ARMOR,
            system="Abune",
            structure_type_id=35825,
            eve_time=now(),
        )
        expected = "Armor timer for Abune - Test (Raitaru)"
        self.assertEqual(str(timer), expected)

    def test_structure_display_name(self):
        timer = Timer(
            details="Test",
            timer_type=Timer.TYPE_ARMOR,
            system="Abune",
            structure_type_id=35825,
            eve_time=now(),
        )
        expected = "Abune - Test (Raitaru)"
        self.assertEqual(timer.structure_display_name, expected)

    def test_label_type_for_timer_type(self):
        timer = Timer(eve_time=now())
        self.assertEqual(timer.label_type_for_timer_type(), "default")

        timer.timer_type = timer.TYPE_ARMOR
        self.assertEqual(timer.label_type_for_timer_type(), "danger")

        timer.timer_type = timer.TYPE_HULL
        self.assertEqual(timer.label_type_for_timer_type(), "danger")

    def test_label_type_for_objective(self):
        timer = Timer(eve_time=now())
        self.assertEqual(timer.label_type_for_objective(), "default")

        timer.objective = Timer.OBJECTIVE_HOSTILE
        self.assertEqual(timer.label_type_for_objective(), "danger")

        timer.objective = Timer.OBJECTIVE_FRIENDLY
        self.assertEqual(timer.label_type_for_objective(), "primary")
