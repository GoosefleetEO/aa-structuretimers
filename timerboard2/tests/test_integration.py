from datetime import timedelta

from django.utils.timezone import now

# from allianceauth.tests.auth_utils import AuthUtils
from django_webtest import WebTest

from . import LoadTestDataMixin, create_test_user
from ..models import Timer


class TestTimerList(LoadTestDataMixin, WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = create_test_user(cls.character_1)
        cls.user_2 = create_test_user(cls.character_2)
        cls.timer_1 = Timer.objects.create(
            details="Timer 1",
            eve_time=now() + timedelta(hours=4),
            eve_character=cls.character_1,
            eve_corp=cls.corporation_1,
            user=cls.user_1,
        )
        cls.timer_2 = Timer.objects.create(
            details="Timer 2",
            eve_time=now() - timedelta(hours=8),
            eve_character=cls.character_1,
            eve_corp=cls.corporation_1,
            user=cls.user_1,
        )
        cls.timer_3 = Timer.objects.create(
            details="Timer 3",
            eve_time=now() - timedelta(hours=8),
            eve_character=cls.character_1,
            eve_corp=cls.corporation_1,
            user=cls.user_1,
        )
