from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)

from eveuniverse.models import EveType


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("basic_access", "Can access this app"),)


class Timer(models.Model):
    """A structure timer"""

    # timer type
    TYPE_NONE = 1
    TYPE_SHIELD = 2
    TYPE_ARMOR = 3
    TYPE_HULL = 4
    TYPE_ANCHORING = 5
    TYPE_UNANCHORING = 6
    TYPE_MOONMINING = 7

    TYPE_CHOICES = (
        (TYPE_NONE, _("None")),
        (TYPE_SHIELD, _("Shield")),
        (TYPE_ARMOR, _("Armor")),
        (TYPE_HULL, _("Hull")),
        (TYPE_ANCHORING, _("Anchoring")),
        (TYPE_UNANCHORING, _("Unanchoring")),
        (TYPE_MOONMINING, _("Moon Mining")),
    )

    # objective
    OBJECTIVE_HOSTILE = 1
    OBJECTIVE_FRIENDLY = 2
    OBJECTIVE_NEUTRAL = 3
    OBJECTIVE_UNDEFINED = 4

    OBJECTIVE_CHOICES = [
        (OBJECTIVE_HOSTILE, _("Hostile")),
        (OBJECTIVE_FRIENDLY, _("Friendly")),
        (OBJECTIVE_NEUTRAL, _("Neutral")),
        (OBJECTIVE_UNDEFINED, _("Undefined")),
    ]

    # visibility
    VISIBILITY_UNRESTRICTED = 1
    VISIBILITY_ALLIANCE = 2
    VISIBILITY_CORPORATION = 3

    VISIBILITY_CHOICES = [
        (VISIBILITY_UNRESTRICTED, _("Unrestricted")),
        (VISIBILITY_ALLIANCE, _("Alliance only")),
        (VISIBILITY_CORPORATION, _("Corporation only")),
    ]

    details = models.CharField(
        max_length=254, default="", verbose_name="structure name"
    )
    timer_type = models.IntegerField(
        choices=TYPE_CHOICES, default=TYPE_NONE, verbose_name="timer type"
    )
    system = models.CharField(
        max_length=254, default="", verbose_name="solar system name"
    )
    planet_moon = models.CharField(
        max_length=254,
        default="",
        blank=True,
        verbose_name="location details",
        help_text=(
            "Additional information about the location of this structure, "
            "e.g. name of nearby planet / moon / gate"
        ),
    )
    structure_type = models.ForeignKey(
        EveType,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        verbose_name="structure type",
    )
    objective_new = models.SmallIntegerField(
        choices=OBJECTIVE_CHOICES, default=OBJECTIVE_UNDEFINED, verbose_name="objective"
    )
    eve_time = models.DateTimeField(
        db_index=True, help_text="Eve time when this timer happens",
    )
    important = models.BooleanField(
        default=False, help_text="Show this timer as important",
    )
    opsec = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "Limit access to users with OPSEC clearance. "
            "Can be combined with visibility."
        ),
    )
    eve_character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        related_name="Timers",
        help_text="Main character of the user who created this timer",
    )
    eve_corp = models.ForeignKey(
        EveCorporationInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name="Timers",
        help_text="Corporation of the user who created this timer",
    )
    eve_alliance = models.ForeignKey(
        EveAllianceInfo,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="Timers",
        help_text="Alliance of the user who created this timer",
    )
    visibility = models.SmallIntegerField(
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_UNRESTRICTED,
        db_index=True,
        help_text=(
            "The visibility of this timer can be limited to members"
            " of your organization"
        ),
    )
    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="Timers",
    )
    fitting_image_url = models.CharField(
        max_length=1024,
        default=None,
        blank=True,
        null=True,
        help_text=(
            "URL to a screenshot of the structure's fitting, "
            "e.g. https://www.example.com/route/image.jpg"
        ),
    )
    owner_name = models.CharField(
        max_length=254,
        default=None,
        blank=True,
        null=True,
        help_text="Name of the corporation owning the structure",
    )

    # the following fields are no longer used
    # but stay in the model for backward compatibility
    structure = models.CharField(
        max_length=254,
        default="",
        blank=True,
        help_text="This field is no longer in use",
    )
    corp_timer = models.BooleanField(
        default=False, blank=True, help_text="This field is no longer in use",
    )
    objective = models.CharField(
        max_length=254,
        default="",
        blank=True,
        help_text="This field is no longer in use",
    )

    class Meta:
        permissions = (("view_opsec_timer", "Can view timers marked as opsec"),)

    @property
    def structure_display_name(self):
        return "{} - {} ({})".format(
            self.system, self.details, self.structure_type.name,
        )

    def __str__(self):
        return "{} timer for {}".format(
            self.get_timer_type_display(), self.structure_display_name,
        )

    def label_type_for_timer_type(self) -> str:
        """returns the Boostrap label type for a timer_type"""
        label_types_map = {
            self.TYPE_NONE: "default",
            self.TYPE_SHIELD: "danger",
            self.TYPE_ARMOR: "danger",
            self.TYPE_HULL: "danger",
            self.TYPE_ANCHORING: "warning",
            self.TYPE_UNANCHORING: "warning",
            self.TYPE_MOONMINING: "success",
        }
        if self.timer_type in label_types_map:
            label_type = label_types_map[self.timer_type]
        else:
            label_type = "default"
        return label_type

    def label_type_for_objective(self) -> str:
        """returns the Boostrap label type for objective"""
        label_types_map = {
            self.OBJECTIVE_FRIENDLY: "primary",
            self.OBJECTIVE_HOSTILE: "danger",
            self.OBJECTIVE_NEUTRAL: "info",
            self.OBJECTIVE_UNDEFINED: "default",
        }
        if self.objective_new in label_types_map:
            label_type = label_types_map[self.objective_new]
        else:
            label_type = "default"
        return label_type
