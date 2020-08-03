from datetime import timedelta
import json
from time import sleep
from typing import Any, List, Tuple

import dhooks_lite
from multiselectfield import MultiSelectField
from simple_mq import SimpleMQ

from django.core.cache import cache
from django.contrib.auth.models import User
from django.db import models, IntegrityError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from allianceauth.eveonline.evelinks import dotlan
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)

from allianceauth.services.hooks import get_extension_logger

from eveuniverse.models import EveSolarSystem, EveType

from . import __title__
from .app_settings import TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS
from .managers import TimerManager
from .utils import (
    LoggerAddTag,
    JsonDateTimeDecoder,
    JsonDateTimeEncoder,
    DATETIME_FORMAT,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("basic_access", "Can access this app"),)


class DiscordWebhook(models.Model):
    """A Discord webhook"""

    ZKB_KILLMAIL_BASEURL = "https://zkillboard.com/kill/"
    ICON_SIZE = 128

    # delay in seconds between every message sent to Discord
    # this needs to be >= 1 to prevent 429 Too Many Request errors
    SEND_DELAY = 2

    name = models.CharField(
        max_length=64, unique=True, help_text="short name to identify this webhook"
    )
    url = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            "URL of this webhook, e.g. "
            "https://discordapp.com/api/webhooks/123456/abcdef"
        ),
    )
    notes = models.TextField(
        null=True,
        default=None,
        blank=True,
        help_text="you can add notes about this webhook here if you want",
    )
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="whether notifications are currently sent to this webhook",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._queue = SimpleMQ(
            cache.get_master_client(), f"{__title__}_webhook_{self.pk}"
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return "{}(id={}, name='{}')".format(
            self.__class__.__name__, self.id, self.name
        )

    def send_message(
        self,
        content: str = None,
        embeds: List[dhooks_lite.Embed] = None,
        tts: bool = None,
        username: str = None,
        avatar_url: str = None,
    ) -> int:
        """Adds Discord message to queue for later sending
        
        Returns updated size of queue
        """
        if embeds:
            embeds_list = [obj.asdict() for obj in embeds]
        else:
            embeds_list = None

        message = {
            "content": content,
            "embeds": embeds_list,
            "tts": tts,
            "username": username,
            "avatar_url": avatar_url,
        }
        return self._queue.enqueue(json.dumps(message, cls=JsonDateTimeEncoder))

    def send_queued_messages(self) -> int:
        """sends all messages in the queue to this webhook
        
        returns number of successfull sent messages

        Killmails that could not be sent are put back into the queue for later retry
        """
        message_count = 0
        while True:
            message_json = self._queue.dequeue()
            if message_json:
                message = json.loads(message_json, cls=JsonDateTimeDecoder)
                logger.debug("Sending message to webhook %s", self)
                sleep(self.SEND_DELAY)
                if self._send_message(message):
                    message_count += 1
                else:
                    self.add_killmail_to_queue(message_json)

            else:
                break

        return message_count

    def queue_size(self) -> int:
        """returns current size of the queue"""
        return self._queue.size()

    def clear_queue(self) -> int:
        """deletes all killmails from the queue. Return number of cleared messages."""
        counter = 0
        while True:
            y = self._queue.dequeue()
            if y is None:
                break
            else:
                counter += 1

        return counter

    def _send_message(self, message: dict) -> bool:
        """send message to webhook
        
        returns True if successful, else False        
        """
        hook = dhooks_lite.Webhook(url=self.url)
        if message.get("embeds"):
            embeds = [
                dhooks_lite.Embed.from_dict(embed_dict)
                for embed_dict in message.get("embeds")
            ]
        else:
            embeds = None

        response = hook.execute(
            content=message.get("content"),
            embeds=embeds,
            username=message.get("username"),
            avatar_url=message.get("avatar_url"),
            wait_for_response=True,
        )
        logger.debug("headers: %s", response.headers)
        logger.debug("status_code: %s", response.status_code)
        logger.debug("content: %s", response.content)
        if response.status_ok:
            return True
        else:
            logger.warning(
                "Failed to send message to Discord. HTTP status code: %d, response: %s",
                response.status_code,
                response.content,
            )
            return False

    @classmethod
    def create_discord_link(cls, name: str, url: str) -> str:
        return f"[{str(name)}]({str(url)})"

    def send_test_message(self) -> Tuple[str, bool]:
        """Sends a test notification to this webhook and returns send report"""
        try:
            message = {"content": f"Test message from {__title__}"}
            success = self._send_message(message)
        except Exception as ex:
            logger.warning(
                "Failed to send test notification to webhook %s: %s",
                self,
                ex,
                exc_info=True,
            )
            return str(ex), False
        else:
            return "(no info)", success

    @staticmethod
    def default_username() -> str:
        """avatar username for all messages"""
        return __title__


class Timer(models.Model):
    """A structure timer"""

    # timer type
    TYPE_NONE = "NO"
    TYPE_ARMOR = "AR"
    TYPE_HULL = "HL"
    TYPE_ANCHORING = "AN"
    TYPE_UNANCHORING = "UA"
    TYPE_MOONMINING = "MM"

    TYPE_CHOICES = (
        (TYPE_NONE, _("None")),
        (TYPE_ARMOR, _("Armor")),
        (TYPE_HULL, _("Hull")),
        (TYPE_ANCHORING, _("Anchoring")),
        (TYPE_UNANCHORING, _("Unanchoring")),
        (TYPE_MOONMINING, _("Moon Mining")),
    )

    # objective
    OBJECTIVE_UNDEFINED = "UN"
    OBJECTIVE_HOSTILE = "HO"
    OBJECTIVE_FRIENDLY = "FR"
    OBJECTIVE_NEUTRAL = "NE"

    OBJECTIVE_CHOICES = [
        (OBJECTIVE_UNDEFINED, _("Undefined")),
        (OBJECTIVE_HOSTILE, _("Hostile")),
        (OBJECTIVE_FRIENDLY, _("Friendly")),
        (OBJECTIVE_NEUTRAL, _("Neutral")),
    ]

    # visibility
    VISIBILITY_UNRESTRICTED = "UN"
    VISIBILITY_ALLIANCE = "AL"
    VISIBILITY_CORPORATION = "CO"

    VISIBILITY_CHOICES = [
        (VISIBILITY_UNRESTRICTED, _("Unrestricted")),
        (VISIBILITY_ALLIANCE, _("Alliance only")),
        (VISIBILITY_CORPORATION, _("Corporation only")),
    ]

    timer_type = models.CharField(
        max_length=2, choices=TYPE_CHOICES, default=TYPE_NONE, verbose_name="timer type"
    )
    eve_solar_system = models.ForeignKey(
        EveSolarSystem, on_delete=models.CASCADE, default=None, null=True
    )
    location_details = models.CharField(
        max_length=254,
        default="",
        blank=True,
        verbose_name="location details",
        help_text=(
            "Additional information about the location of this structure, "
            "e.g. name of nearby planet / moon / gate"
        ),
    )
    structure_type = models.ForeignKey(EveType, on_delete=models.CASCADE,)
    structure_name = models.CharField(max_length=254, default="", blank=True)
    objective = models.CharField(
        max_length=2,
        choices=OBJECTIVE_CHOICES,
        default=OBJECTIVE_UNDEFINED,
        verbose_name="objective",
    )
    date = models.DateTimeField(
        db_index=True, help_text="Date when this timer happens",
    )
    is_important = models.BooleanField(
        default=False, help_text="Mark this timer as is_important",
    )
    owner_name = models.CharField(
        max_length=254,
        default=None,
        blank=True,
        null=True,
        help_text="Name of the corporation owning the structure",
    )
    is_opsec = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "Limit access to users with OPSEC clearance. "
            "Can be combined with visibility."
        ),
    )
    eve_character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="Timers",
        help_text="Main character of the user who created this timer",
    )
    eve_corporation = models.ForeignKey(
        EveCorporationInfo,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="Timers",
        help_text="Corporation of the user who created this timer",
    )
    eve_alliance = models.ForeignKey(
        EveAllianceInfo,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="Timers",
        help_text="Alliance of the user who created this timer",
    )
    visibility = models.CharField(
        max_length=2,
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
    details_image_url = models.CharField(
        max_length=1024,
        default=None,
        blank=True,
        null=True,
        help_text=(
            "URL for details like a screenshot of the structure's fitting, "
            "e.g. https://www.example.com/route/image.jpg"
        ),
    )
    details_notes = models.TextField(
        default="",
        blank=True,
        help_text="Notes with additional information about this timer",
    )

    objects = TimerManager()

    class Meta:
        permissions = (("view_opsec_timer", "Can view timers marked as is_opsec"),)

    @property
    def structure_display_name(self):
        return "{}{} ({})".format(
            self.eve_solar_system.name,
            f" - {self.location_details}" if self.location_details else "",
            self.structure_type.name,
        )

    def __str__(self):
        return "{} timer for {}".format(
            self.get_timer_type_display(), self.structure_display_name,
        )

    def label_type_for_timer_type(self) -> str:
        """returns the Boostrap label type for a timer_type"""
        label_types_map = {
            self.TYPE_NONE: "default",
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
        if self.objective in label_types_map:
            label_type = label_types_map[self.objective]
        else:
            label_type = "default"
        return label_type


class NotificationRule(models.Model):

    MINUTES_0 = 0
    MINUTES_5 = 5
    MINUTES_15 = 15
    MINUTES_30 = 30
    MINUTES_CHOICES = (
        (MINUTES_0, "0"),
        (MINUTES_5, "5"),
        (MINUTES_15, "15"),
        (MINUTES_30, "30"),
    )
    PING_TYPE_NONE = "PN"
    PING_TYPE_HERE = "PH"
    PING_TYPE_EVERYBODY = "PE"
    PING_TYPE_CHOICES = (
        (PING_TYPE_NONE, "(no ping)"),
        (PING_TYPE_HERE, "@here"),
        (PING_TYPE_EVERYBODY, "@everybody"),
    )

    minutes = models.PositiveIntegerField(
        choices=MINUTES_CHOICES,
        help_text="Time before event in minutes when notifications are sent",
    )
    webhooks = models.ManyToManyField(
        DiscordWebhook, help_text="Webhooks notifications are sent to"
    )
    ping_type = models.CharField(
        max_length=2,
        choices=PING_TYPE_CHOICES,
        default=PING_TYPE_NONE,
        help_text="Options for pinging for every notification",
    )
    is_enabled = models.BooleanField(
        default=True, help_text="whether this rule is currently active",
    )
    require_timer_types = MultiSelectField(
        choices=Timer.TYPE_CHOICES,
        blank=True,
        help_text=(
            "Timer must have one of the given timer types "
            "or leave blank to match any."
        ),
    )
    require_objectives = MultiSelectField(
        choices=Timer.OBJECTIVE_CHOICES,
        blank=True,
        help_text=(
            "Timer must have one of the given objectives "
            "or leave blank to match any."
        ),
    )
    require_corporations = models.ManyToManyField(
        EveCorporationInfo,
        blank=True,
        help_text=(
            "Timer must be created by one of the given corporations "
            "or leave blank to match any."
        ),
    )
    require_alliances = models.ManyToManyField(
        EveAllianceInfo,
        blank=True,
        help_text=(
            "Timer must be created by one of the given alliances "
            "or leave blank to match any."
        ),
    )

    def __str__(self) -> str:
        return f"Notification Rule #{self.id}"

    def process_timers(self):
        from .tasks import send_messages_for_webhook

        threshold_date = now() - timedelta(
            minutes=TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS
        )
        for timer in Timer.objects.filter(date__gt=threshold_date).exclude(
            timernotificationprocessed__notification_rule=self
        ):
            if timer.date - timedelta(minutes=self.minutes) < now():
                is_matching = True
            else:
                is_matching = False

            if is_matching and self.require_timer_types:
                is_matching = timer.timer_type in self.require_timer_types

            if is_matching and self.require_objectives:
                is_matching = timer.objective in self.require_objectives

            if is_matching and self.require_corporations.count() > 0:
                is_matching = timer.eve_corporation in self.require_corporations.all()

            if is_matching and self.require_alliances.count() > 0:
                is_matching = timer.eve_alliance in self.require_alliances.all()

            if is_matching:
                for webhook in self.webhooks.filter(is_enabled=True):
                    self.send_timer_notification(webhook, timer)
                    send_messages_for_webhook.delay(webhook_pk=webhook.pk)
                    try:
                        TimerNotificationProcessed.objects.create(
                            timer=timer, notification_rule=self
                        )
                    except IntegrityError:
                        pass

    def send_timer_notification(self, webhook: DiscordWebhook, timer: Timer) -> None:
        """sends notification for given timer to given webhook"""
        minutes = round((now() - timer.date).total_seconds() / 60)
        content = f"The following timer is coming out in less than {minutes} minutes:"

        structure_type_name = timer.structure_type.name
        solar_system_name = timer.eve_solar_system.name
        title = f"{structure_type_name} in {solar_system_name}"

        region_name = timer.eve_solar_system.eve_constellation.eve_region.name
        solar_system_link = webhook.create_discord_link(
            name=solar_system_name, url=dotlan.solar_system_url(solar_system_name)
        )
        solar_system_text = f"{solar_system_link} ({region_name})"
        near_text = f" near {timer.location_details}" if timer.location_details else ""
        owned_text = f" owned by **{timer.owner_name}**" if timer.owner_name else ""
        description = (
            f"An **{structure_type_name}** in {solar_system_text}{near_text}{owned_text} "
            f"is coming out of **{timer.get_timer_type_display()}** timer at "
            f"**{timer.date.strftime(DATETIME_FORMAT)}**. "
            f"Our stance is **{timer.get_objective_display()}**."
        )
        structure_icon_url = timer.structure_type.icon_url(size=128)
        embed = dhooks_lite.Embed(
            title=title,
            description=description,
            thumbnail=dhooks_lite.Thumbnail(structure_icon_url),
        )
        webhook.send_message(content=content, embeds=[embed])

    @classmethod
    def get_timer_type_display(cls, value: Any) -> str:
        return cls._get_multiselect_display(value, Timer.TYPE_CHOICES)

    @classmethod
    def get_objectives_display(cls, value: Any) -> str:
        return cls._get_multiselect_display(value, Timer.OBJECTIVE_CHOICES)

    @classmethod
    def _get_multiselect_display(
        cls, value: Any, choices: List[Tuple[Any, str]]
    ) -> str:
        for choice, text in choices:
            if str(choice) == str(value):
                return text

        raise ValueError(f"Invalid choice: {value}")


class TimerNotificationProcessed(models.Model):

    timer = models.ForeignKey(Timer, on_delete=models.CASCADE)
    notification_rule = models.ForeignKey(NotificationRule, on_delete=models.CASCADE)
