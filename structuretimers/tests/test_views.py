from datetime import timedelta
import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.timezone import now

from ..models import Timer
from .. import views
from . import LoadTestDataMixin, create_test_user, add_permission_to_user_by_name


MODULE_PATH = "structures.views"


def get_json_response(response: object):
    return json.loads(response.content.decode("utf-8"))


@patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
class TestViewBase(LoadTestDataMixin, TestCase):
    @patch("structuretimers.models.STRUCTURETIMERS_NOTIFICATIONS_ENABLED", False)
    def setUp(self):
        self.factory = RequestFactory()

        # user
        self.user_1 = create_test_user(self.character_1)
        self.user_2 = create_test_user(self.character_2)
        self.user_2 = add_permission_to_user_by_name(
            "structuretimers.manage_timer", self.user_2
        )
        self.user_3 = create_test_user(self.character_3)

        # timers
        self.timer_1 = Timer(
            structure_name="Timer 1",
            location_details="Near the star",
            date=now() + timedelta(hours=4),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            owner_name="Big Boss",
            details_image_url="http://www.example.com/dummy.png",
            details_notes="Some notes",
        )
        self.timer_1.save()
        self.timer_2 = Timer(
            structure_name="Timer 2",
            date=now() - timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_1,
            eve_solar_system=self.system_abune,
            structure_type=self.type_raitaru,
            is_important=True,
        )
        self.timer_2.save()
        self.timer_3 = Timer(
            structure_name="Timer 3",
            date=now() - timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_1,
            eve_solar_system=self.system_enaluri,
            structure_type=self.type_astrahus,
        )
        self.timer_3.save()


class TestListData(TestViewBase):
    def _send_request(self, tab_name: str = "current", user: User = None) -> set:
        if not user:
            user = self.user_1

        request = self.factory.get(
            reverse("structuretimers:timer_list_data", args=[tab_name])
        )
        request.user = user
        response = views.timer_list_data(request, tab_name)
        self.assertEqual(response.status_code, 200)
        return {x["id"] for x in get_json_response(response)}

    def test_timer_list_view_loads(self):
        request = self.factory.get(reverse("structuretimers:timer_list"))
        request.user = self.user_1
        response = views.timer_list(request)
        self.assertEqual(response.status_code, 200)

    def test_timer_list_data_current_and_past(self):
        # test current timers
        timer_ids = self._send_request("current")
        expected = {self.timer_1.id}
        self.assertSetEqual(timer_ids, expected)

        # test past timers
        timer_ids = self._send_request("past")
        expected = {self.timer_2.id, self.timer_3.id}
        self.assertSetEqual(timer_ids, expected)

    def test_show_corp_restricted_to_corp_member(self):
        timer_4 = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            user=self.user_2,
            visibility=Timer.VISIBILITY_CORPORATION,
        )
        timer_4.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id, timer_4.id}
        self.assertSetEqual(timer_ids, expected)

    def test_dont_show_corp_restricted_to_non_corp_member(self):
        timer = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_corporation=self.corporation_3,
            user=self.user_3,
            visibility=Timer.VISIBILITY_CORPORATION,
        )
        timer.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id}
        self.assertSetEqual(timer_ids, expected)

    def test_show_alliance_restricted_to_alliance_member(self):
        timer_4 = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_1,
            eve_corporation=self.corporation_1,
            eve_alliance=self.alliance_1,
            user=self.user_2,
            visibility=Timer.VISIBILITY_ALLIANCE,
        )
        timer_4.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id, timer_4.id}
        self.assertSetEqual(timer_ids, expected)

    def test_dont_show_alliance_restricted_to_non_alliance_member(self):
        timer = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_corporation=self.corporation_3,
            eve_alliance=self.alliance_3,
            user=self.user_3,
            visibility=Timer.VISIBILITY_ALLIANCE,
        )
        timer.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id}
        self.assertSetEqual(timer_ids, expected)

    def test_show_opsec_restricted_to_opsec_member(self):
        self.user_1 = add_permission_to_user_by_name(
            "structuretimers.opsec_access", self.user_1
        )
        timer_4 = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_corporation=self.corporation_3,
            user=self.user_3,
            is_opsec=True,
        )
        timer_4.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id, timer_4.id}
        self.assertSetEqual(timer_ids, expected)

    def test_dont_show_opsec_restricted_to_non_opsec_member(self):
        timer = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_corporation=self.corporation_3,
            user=self.user_3,
            is_opsec=True,
        )
        timer.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id}
        self.assertSetEqual(timer_ids, expected)

    def test_dont_show_opsec_corp_restricted_to_opsec_member_other_corp(self):
        self.user_1 = add_permission_to_user_by_name(
            "structuretimers.opsec_access", self.user_1
        )
        timer = Timer(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_corporation=self.corporation_3,
            user=self.user_3,
            is_opsec=True,
            visibility=Timer.VISIBILITY_CORPORATION,
        )
        timer.save()
        timer_ids = self._send_request()
        expected = {self.timer_1.id}
        self.assertSetEqual(timer_ids, expected)

    def test_show_corp_timer_to_creator_of_different_corp(self):
        timer_4 = Timer.objects.create(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_corporation=self.corporation_3,
            visibility=Timer.VISIBILITY_CORPORATION,
            user=self.user_1,
        )
        timer_ids = self._send_request()
        expected = {self.timer_1.id, timer_4.id}
        self.assertSetEqual(timer_ids, expected)

    def test_show_alliance_timer_to_creator_of_different_alliance(self):
        timer_4 = Timer.objects.create(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
            eve_character=self.character_3,
            eve_alliance=self.alliance_3,
            eve_corporation=self.corporation_3,
            visibility=Timer.VISIBILITY_ALLIANCE,
            user=self.user_1,
        )
        timer_ids = self._send_request()
        expected = {self.timer_1.id, timer_4.id}
        self.assertSetEqual(timer_ids, expected)

    def test_can_show_timers_without_user_character_corporation_or_alliance(self):
        timer_4 = Timer.objects.create(
            structure_name="Timer 4",
            eve_solar_system=self.system_abune,
            structure_type=self.type_astrahus,
            date=now() + timedelta(hours=8),
        )
        timer_ids = self._send_request()
        expected = {self.timer_1.id, timer_4.id}
        self.assertSetEqual(timer_ids, expected)

    def test_list_for_manager(self):
        timer_ids = self._send_request(user=self.user_2)
        expected = {self.timer_1.id}
        self.assertSetEqual(timer_ids, expected)


class TestGetTimerData(TestViewBase):
    def test_normal(self):
        request = self.factory.get(
            reverse("structuretimers:get_timer_data", args=[self.timer_1.pk])
        )
        request.user = self.user_1
        response = views.get_timer_data(request, self.timer_1.pk)
        self.assertEqual(response.status_code, 200)

    def test_forbidden(self):
        self.timer_1.is_opsec = True
        self.timer_1.save()
        request = self.factory.get(
            reverse("structuretimers:get_timer_data", args=[self.timer_1.pk])
        )
        request.user = self.user_3
        response = views.get_timer_data(request, self.timer_1.pk)
        self.assertEqual(response.status_code, 403)


class TestSelect2Views(LoadTestDataMixin, TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.user_1 = create_test_user(cls.character_1)

    def test_select2_solar_systems_normal(self):
        request = self.factory.get(
            reverse("structuretimers:select2_solar_systems"), data={"term": "abu"}
        )
        request.user = self.user_1
        response = views.select2_solar_systems(request)
        self.assertEqual(response.status_code, 200)
        data = get_json_response(response)
        self.assertEqual(data, {"results": [{"id": 30004984, "text": "Abune"}]})

    def test_select2_solar_systems_empty(self):
        request = self.factory.get(reverse("structuretimers:select2_solar_systems"))
        request.user = self.user_1
        response = views.select2_solar_systems(request)
        self.assertEqual(response.status_code, 200)
        data = get_json_response(response)
        self.assertEqual(data, {"results": None})

    def test_select2_structure_types_normal(self):
        request = self.factory.get(
            reverse("structuretimers:select2_structure_types"), data={"term": "ast"}
        )
        request.user = self.user_1
        response = views.select2_structure_types(request)
        self.assertEqual(response.status_code, 200)
        data = get_json_response(response)
        self.assertEqual(data, {"results": [{"id": 35832, "text": "Astrahus"}]})

    def test_select2_structure_types_empty(self):
        request = self.factory.get(reverse("structuretimers:select2_structure_types"))
        request.user = self.user_1
        response = views.select2_structure_types(request)
        self.assertEqual(response.status_code, 200)
        data = get_json_response(response)
        self.assertEqual(data, {"results": None})
