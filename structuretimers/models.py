import json
from time import sleep
from urllib.parse import urljoin
from typing import Any, List, Tuple

import dhooks_lite
from multiselectfield import MultiSelectField
from simple_mq import SimpleMQ

from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import models
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
from .app_settings import TIMERBOARD2_NOTIFICATIONS_ENABLED
from .managers import NotificationRuleManager, TimerManager
from .utils import (
    LoggerAddTag,
    JSONDateTimeDecoder,
    JSONDateTimeEncoder,
    DATETIME_FORMAT,
    get_site_base_url,
)

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


def default_avatar_url() -> str:
    """avatar url for all messages"""
    return urljoin(
        get_site_base_url(),
        staticfiles_storage.url("structuretimers/structuretimers_logo.png"),
    )


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("timer_management", "Can create and edit timers"),
        )


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
        self._main_queue = SimpleMQ(
            cache.get_master_client(), f"{__title__}_webhook_{self.pk}_main"
        )
        self._error_queue = SimpleMQ(
            cache.get_master_client(), f"{__title__}_webhook_{self.pk}_errors"
        )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"

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
        Raises ValueError if mesage is incomplete
        """
        if not content and not embeds:
            raise ValueError("Message must have content or embeds to be valid")

        if embeds:
            embeds_list = [obj.asdict() for obj in embeds]
        else:
            embeds_list = None

        message = dict()
        if content:
            message["content"] = content
        if embeds_list:
            message["embeds"] = embeds_list
        if tts:
            message["tts"] = tts
        if username:
            message["username"] = username
        if avatar_url:
            message["avatar_url"] = avatar_url

        return self._main_queue.enqueue(json.dumps(message, cls=JSONDateTimeEncoder))

    def send_queued_messages(self) -> int:
        """sends all messages in the queue to this webhook
        
        returns number of successfull sent messages

        Messages that could not be sent are put back into the queue for later retry
        """
        message_count = 0
        while True:
            message_json = self._main_queue.dequeue()
            if message_json:
                message = json.loads(message_json, cls=JSONDateTimeDecoder)
                logger.debug("Sending message to webhook %s", self)
                if self.send_message_to_webhook(message):
                    message_count += 1
                else:
                    self._error_queue.enqueue(message_json)

                sleep(self.SEND_DELAY)

            else:
                break

        while True:
            message_json = self._error_queue.dequeue()
            if message_json:
                self._main_queue.enqueue(message_json)
            else:
                break

        return message_count

    def queue_size(self) -> int:
        """returns current size of the queue"""
        return self._main_queue.size()

    def clear_queue(self) -> int:
        """deletes all messages from the queue. Returns number of cleared messages."""
        counter = 0
        while True:
            y = self._main_queue.dequeue()
            if y is None:
                break
            else:
                counter += 1

        return counter

    def send_message_to_webhook(self, message: dict) -> bool:
        """sends message directly to webhook
        
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
            message = {
                "content": f"Test message from {__title__}",
                "username": __title__,
                "avatar_url": default_avatar_url(),
            }
            success = self.send_message_to_webhook(message)
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
    TYPE_FINAL = "FI"
    TYPE_ANCHORING = "AN"
    TYPE_UNANCHORING = "UA"
    TYPE_MOONMINING = "MM"

    TYPE_CHOICES = (
        (TYPE_NONE, _("Unspecified")),
        (TYPE_ARMOR, _("Armor")),
        (TYPE_HULL, _("Hull")),
        (TYPE_FINAL, _("Final")),
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
        (OBJECTIVE_UNDEFINED, _("undefined")),
        (OBJECTIVE_HOSTILE, _("hostile")),
        (OBJECTIVE_FRIENDLY, _("friendly")),
        (OBJECTIVE_NEUTRAL, _("neutral")),
    ]

    # visibility
    VISIBILITY_UNRESTRICTED = "UN"
    VISIBILITY_ALLIANCE = "AL"
    VISIBILITY_CORPORATION = "CO"

    VISIBILITY_CHOICES = [
        (VISIBILITY_UNRESTRICTED, _("unrestricted")),
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
    notification_rules = models.ManyToManyField(
        "NotificationRule",
        through="ScheduledNotification",
        through_fields=("timer", "notification_rule"),
        help_text="Notification rules conforming with this timer",
    )

    objects = TimerManager()

    class Meta:
        permissions = (("view_opsec_timer", "Can view timers marked as is_opsec"),)

    def __str__(self):
        return "%s timer for %s @ %s" % (
            self.get_timer_type_display(),
            self.structure_display_name,
            self.date.strftime(DATETIME_FORMAT),
        )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        date_changed = False
        if TIMERBOARD2_NOTIFICATIONS_ENABLED and not is_new:
            try:
                date_changed = self.date != Timer.objects.get(pk=self.pk).date
            except Timer.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        if TIMERBOARD2_NOTIFICATIONS_ENABLED and (is_new or date_changed):
            self._import_schedule_notifications_for_timer().delay(timer_pk=self.pk)

    @staticmethod
    def _import_schedule_notifications_for_timer() -> object:
        from .tasks import schedule_notifications_for_timer

        return schedule_notifications_for_timer

    @property
    def structure_display_name(self):
        return "{}{} in {}{}".format(
            self.structure_type.name,
            f' "{self.structure_name}"' if self.structure_name else "",
            self.eve_solar_system.name,
            f" near {self.location_details}" if self.location_details else "",
        )

    def label_type_for_timer_type(self) -> str:
        """returns the Boostrap label type for a timer_type"""
        label_types_map = {
            self.TYPE_NONE: "default",
            self.TYPE_ARMOR: "danger",
            self.TYPE_HULL: "danger",
            self.TYPE_FINAL: "danger",
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

    def send_notification(self, webhook: DiscordWebhook, ping_text: str = None) -> None:
        """sends notification for given self to given webhook"""
        content = f"{ping_text} " if ping_text else ""
        minutes = round((self.date - now()).total_seconds() / 60)
        mod_text = "**important** " if self.is_important else ""
        content += (
            f"The following {mod_text}structure timer will elapse "
            f"in less than **{minutes:,}** minutes:"
        )

        structure_type_name = self.structure_type.name
        solar_system_name = self.eve_solar_system.name
        title = f"{structure_type_name} in {solar_system_name}"
        if self.structure_name:
            structure_name_text = f'**{structure_type_name}** "{self.structure_name}"'
        else:
            article = "an" if structure_type_name[0:1].lower() in "aeiou" else "a"
            structure_name_text = f"{article} **{structure_type_name}**"

        region_name = self.eve_solar_system.eve_constellation.eve_region.name
        solar_system_link = webhook.create_discord_link(
            name=solar_system_name, url=dotlan.solar_system_url(solar_system_name)
        )
        solar_system_text = f"{solar_system_link} ({region_name})"
        near_text = f" near {self.location_details}" if self.location_details else ""
        owned_text = f" owned by **{self.owner_name}**" if self.owner_name else ""
        description = (
            f"The **{self.get_timer_type_display()}** timer for "
            f"{structure_name_text} in {solar_system_text}{near_text}{owned_text} "
            f"will elapse at **{self.date.strftime(DATETIME_FORMAT)}**. "
            f"Our stance is: **{self.get_objective_display()}**."
        )
        structure_icon_url = self.structure_type.icon_url(size=128)
        if self.objective == self.OBJECTIVE_FRIENDLY:
            color = int("0x375a7f", 16)
        elif self.objective == self.OBJECTIVE_HOSTILE:
            color = int("0xd9534f", 16)
        else:
            color = None

        embed = dhooks_lite.Embed(
            title=title,
            description=description,
            thumbnail=dhooks_lite.Thumbnail(structure_icon_url),
            color=color,
        )
        webhook.send_message(
            content=content,
            embeds=[embed],
            username=__title__,
            avatar_url=default_avatar_url(),
        )


class NotificationRule(models.Model):

    MINUTES_0 = 0
    MINUTES_5 = 5
    MINUTES_10 = 10
    MINUTES_15 = 15
    MINUTES_30 = 30
    MINUTES_45 = 45
    MINUTES_60 = 60
    MINUTES_120 = 120

    MINUTES_CHOICES = (
        (MINUTES_0, "0"),
        (MINUTES_5, "5"),
        (MINUTES_10, "10"),
        (MINUTES_15, "15"),
        (MINUTES_30, "30"),
        (MINUTES_45, "45"),
        (MINUTES_60, "60"),
        (MINUTES_120, "120"),
    )
    PING_TYPE_NONE = "PN"
    PING_TYPE_HERE = "PH"
    PING_TYPE_EVERYONE = "PE"
    PING_TYPE_CHOICES = (
        (PING_TYPE_NONE, "(no ping)"),
        (PING_TYPE_HERE, "@here"),
        (PING_TYPE_EVERYONE, "@everyone"),
    )

    minutes = models.PositiveIntegerField(
        choices=MINUTES_CHOICES,
        db_index=True,
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

    objects = NotificationRuleManager()

    def __str__(self) -> str:
        return f"Notification Rule #{self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if TIMERBOARD2_NOTIFICATIONS_ENABLED and self.is_enabled:
            self._import_scheduled_notifications_for_rule().delay(
                notification_rule_pk=self.pk
            )

    @staticmethod
    def _import_scheduled_notifications_for_rule() -> object:
        from .tasks import scheduled_notifications_for_rule

        return scheduled_notifications_for_rule

    @property
    def ping_type_text(self) -> str:
        return self.ping_type_to_text(self.ping_type)

    def is_matching_timer(self, timer: "Timer") -> bool:
        """returns True if notification rule is matching the given timer, else False"""
        is_matching = True
        if is_matching and self.require_timer_types:
            is_matching = timer.timer_type in self.require_timer_types

        if is_matching and self.require_objectives:
            is_matching = timer.objective in self.require_objectives

        if is_matching and self.require_corporations.count() > 0:
            is_matching = timer.eve_corporation in self.require_corporations.all()

        if is_matching and self.require_alliances.count() > 0:
            is_matching = timer.eve_alliance in self.require_alliances.all()

        return is_matching

    @classmethod
    def ping_type_to_text(cls, ping_type: str) -> str:
        """returns the text for creating the given ping on Discord"""
        my_map = {
            NotificationRule.PING_TYPE_NONE: "",
            NotificationRule.PING_TYPE_HERE: "@here",
            NotificationRule.PING_TYPE_EVERYONE: "@everyone",
        }
        return my_map[ping_type] if ping_type in my_map else ""

    @staticmethod
    def _import_send_messages_for_webhook() -> object:
        from .tasks import send_messages_for_webhook

        return send_messages_for_webhook

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


class ScheduledNotification(models.Model):
    """A scheduled notification task"""

    timer = models.ForeignKey(Timer, on_delete=models.CASCADE)
    notification_rule = models.ForeignKey(NotificationRule, on_delete=models.CASCADE)
    timer_date = models.DateTimeField(db_index=True)
    notification_date = models.DateTimeField(db_index=True)
    celery_task_id = models.CharField(max_length=765, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["timer", "notification_rule"],
                name="unique_notification_schedule",
            )
        ]

    def __repr__(self) -> str:
        return (
            f"ScheduledNotification(timer='{self.timer}', "
            f"notification_rule='{self.notification_rule}', "
            f"celery_task_id='{self.celery_task_id}', "
            f"timer_date='{self.timer_date}', "
            f"timer_date='{self.notification_date}')"
        )
