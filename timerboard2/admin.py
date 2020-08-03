from django.contrib import admin
from django.db.models.functions import Lower

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from .models import DiscordWebhook, NotificationRule, Timer
from . import tasks


@admin.register(DiscordWebhook)
class DiscordWebhookAdmin(admin.ModelAdmin):
    list_display = ("name", "is_enabled", "_messages_in_queue")
    list_filter = ("is_enabled",)

    def _messages_in_queue(self, obj):
        return obj.queue_size()

    actions = ["send_test_message", "purge_messages"]

    def purge_messages(self, request, queryset):
        actions_count = 0
        killmails_deleted = 0
        for webhook in queryset:
            killmails_deleted += webhook.clear_queue()
            actions_count += 1

        self.message_user(
            request,
            f"Purged queued messages for {actions_count} webhooks, "
            f"deleting a total of {killmails_deleted} messages.",
        )

    purge_messages.short_description = "Purge queued messages of selected webhooks"

    def send_test_message(self, request, queryset):
        actions_count = 0
        for webhook in queryset:
            tasks.send_test_message_to_webhook.delay(webhook.pk, request.user.pk)
            actions_count += 1

        self.message_user(
            request,
            f"Initiated sending of {actions_count} test messages to "
            f"selected webhooks. You will receive a notification with the result.",
        )

    send_test_message.short_description = "Send test message to selected webhooks"


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_enabled",
        "minutes",
        "_require_timer_type",
        "_require_objectives",
        "_require_corporations",
        "_require_alliances",
        "_webhooks",
        "ping_type",
    )
    list_filter = ("is_enabled",)

    def _require_timer_type(_, obj):
        return [
            NotificationRule.get_timer_type_display(x) for x in obj.require_timer_types
        ]

    def _require_objectives(_, obj):
        return [
            NotificationRule.get_objectives_display(x) for x in obj.require_objectives
        ]

    def _require_corporations(_, obj):
        return list(
            obj.require_corporations.values_list(
                "corporation_name", flat=True
            ).order_by("corporation_name")
        )

    def _webhooks(_, obj):
        return list(obj.webhooks.values_list("name", flat=True).order_by("name"))

    def _require_alliances(_, obj):
        return list(
            obj.require_alliances.values_list("alliance_name", flat=True).order_by(
                "alliance_name"
            )
        )

    filter_horizontal = ("require_alliances", "require_corporations", "webhooks")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """overriding this formfield to have sorted lists in the form"""
        if db_field.name == "require_alliances":
            kwargs["queryset"] = EveAllianceInfo.objects.all().order_by(
                Lower("alliance_name")
            )

        elif db_field.name == "require_corporations":
            kwargs["queryset"] = EveCorporationInfo.objects.all().order_by(
                Lower("corporation_name")
            )

        elif db_field.name == "webhooks":
            kwargs["queryset"] = DiscordWebhook.objects.all().order_by(Lower("name"))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    pass
