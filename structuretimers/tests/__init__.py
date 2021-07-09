"""Utility functions and classes for tests"""

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from eveuniverse.models import EveSolarSystem, EveType

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.tests.auth_utils import AuthUtils

from ..models import DistancesFromStaging, StagingSystem, Timer
from .testdata.load_eveuniverse import load_eveuniverse


def add_main_to_user(user: User, character: EveCharacter):
    CharacterOwnership.objects.create(
        user=user, owner_hash="x1" + character.character_name, character=character
    )
    user.profile.main_character = character
    user.profile.save()


def create_test_user(character: EveCharacter) -> User:
    User.objects.filter(username=character.character_name).delete()
    user = AuthUtils.create_user(character.character_name)
    add_main_to_user(user, character)
    AuthUtils.add_permission_to_user_by_name("structuretimers.basic_access", user)
    user = User.objects.get(pk=user.pk)
    return user


def add_permission_to_user_by_name(
    perm: str, user: User, disconnect_signals=False
) -> User:
    """adds permission to given user by name and returns updated user object"""
    AuthUtils.add_permission_to_user_by_name(perm, user)
    return User.objects.get(pk=user.pk)


class LoadTestDataMixin:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        load_eveuniverse()
        cls.type_astrahus = EveType.objects.get(id=35832)
        cls.type_raitaru = EveType.objects.get(id=35825)
        cls.system_abune = EveSolarSystem.objects.get(id=30004984)
        cls.system_enaluri = EveSolarSystem.objects.get(id=30045339)

        EveCharacter.objects.filter(character_id__in=[1001, 1002, 1003]).delete()
        EveCorporationInfo.objects.filter(corporation_id__in=[2001, 2003]).delete()
        EveAllianceInfo.objects.filter(alliance_id__in=[3001, 3003]).delete()
        cls.character_1 = EveCharacter.objects.create(
            character_id=1001,
            character_name="Bruce Wayne",
            corporation_id=2001,
            corporation_name="Wayne Technologies",
            alliance_id=3001,
            alliance_name="Wayne Enterprises",
        )
        cls.corporation_1 = EveCorporationInfo.objects.create(
            corporation_id=cls.character_1.corporation_id,
            corporation_name=cls.character_1.corporation_name,
            member_count=99,
        )
        cls.alliance_1 = EveAllianceInfo.objects.create(
            alliance_id=cls.character_1.alliance_id,
            alliance_name=cls.character_1.alliance_name,
            executor_corp_id=cls.corporation_1.corporation_id,
        )
        cls.character_2 = EveCharacter.objects.create(
            character_id=1002,
            character_name="Clark Kent",
            corporation_id=2001,
            corporation_name="Wayne Technologies",
            alliance_id=3001,
            alliance_name="Wayne Enterprises",
        )
        cls.character_3 = EveCharacter.objects.create(
            character_id=1003,
            character_name="Lex Luthor",
            corporation_id=2003,
            corporation_name="Lex Corp",
            alliance_id=3003,
            alliance_name="Lex Holding",
        )
        cls.corporation_3 = EveCorporationInfo.objects.create(
            corporation_id=cls.character_3.corporation_id,
            corporation_name=cls.character_3.corporation_name,
            member_count=666,
        )
        cls.alliance_3 = EveAllianceInfo.objects.create(
            alliance_id=cls.character_3.alliance_id,
            alliance_name=cls.character_3.alliance_name,
            executor_corp_id=cls.corporation_3.corporation_id,
        )


def create_fake_timer(*args, **kwargs):
    with patch(
        "structuretimers.models._task_calc_timer_distances_for_all_staging_systems",
        Mock(),
    ):
        if "light_years" in kwargs:
            light_years = kwargs.pop("light_years")
        else:
            light_years = None
        if "jumps" in kwargs:
            jumps = kwargs.pop("jumps")
        else:
            jumps = None
        if "enabled_notifications" in kwargs:
            kwargs.pop("enabled_notifications")
            timer = Timer.objects.create(*args, **kwargs)
        else:
            with patch(
                "structuretimers.models._task_schedule_notifications_for_timer", Mock()
            ):
                timer = Timer.objects.create(*args, **kwargs)
        if light_years or jumps:
            for staging_system in StagingSystem.objects.all():
                DistancesFromStaging.objects.update_or_create(
                    staging_system=staging_system,
                    timer=timer,
                    defaults={"light_years": light_years, "jumps": jumps},
                )
        return timer


def create_fake_staging_system(*args, **kwargs):
    if "light_years" in kwargs:
        light_years = kwargs.pop("light_years")
    else:
        light_years = None
    if "jumps" in kwargs:
        jumps = kwargs.pop("jumps")
    else:
        jumps = None
    with patch("structuretimers.models._task_calc_staging_system", Mock()):
        staging_system = StagingSystem.objects.create(*args, **kwargs)
        if light_years or jumps:
            for timer in Timer.objects.all():
                DistancesFromStaging.objects.update_or_create(
                    staging_system=staging_system,
                    timer=timer,
                    defaults={"light_years": light_years, "jumps": jumps},
                )
        return staging_system
