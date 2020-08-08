from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.db.models.functions import Lower
from django.utils.timezone import now
from django.utils.safestring import mark_safe

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from .models import DiscordWebhook, NotificationRule, ScheduledNotification, Timer
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


def make_nice(name: str) -> str:
    return name.replace("_", " ").capitalize()


class NotificationRuleAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        self._validate_not_same_options_chosen(
            cleaned_data,
            "require_timer_types",
            "exclude_timer_types",
            lambda x: NotificationRule.get_multiselect_display(x, Timer.TYPE_CHOICES),
        )
        self._validate_not_same_options_chosen(
            cleaned_data,
            "require_objectives",
            "exclude_objectives",
            lambda x: NotificationRule.get_multiselect_display(
                x, Timer.OBJECTIVE_CHOICES
            ),
        )
        self._validate_not_same_options_chosen(
            cleaned_data,
            "require_visibility",
            "exclude_visibility",
            lambda x: NotificationRule.get_multiselect_display(
                x, Timer.VISIBILITY_CHOICES
            ),
        )
        self._validate_not_same_options_chosen(
            cleaned_data, "require_corporations", "exclude_corporations", lambda x: x,
        )
        self._validate_not_same_options_chosen(
            cleaned_data, "require_alliances", "exclude_alliances", lambda x: x,
        )

    @staticmethod
    def _validate_not_same_options_chosen(
        cleaned_data, field_name_1, field_name_2, display_func
    ) -> None:
        same_options = set(cleaned_data[field_name_1]).intersection(
            set(cleaned_data[field_name_2])
        )
        if same_options:
            same_options_text = ", ".join(
                map(str, [display_func(x) for x in same_options],)
            )
            raise ValidationError(
                f"Can not choose same options for {make_nice(field_name_1)} "
                f"& {make_nice(field_name_2)}: {same_options_text}"
            )


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    form = NotificationRuleAdminForm
    list_display = (
        "id",
        "is_enabled",
        "minutes",
        "_webhooks",
        "ping_type",
        "_clauses",
    )
    list_filter = ("is_enabled",)

    def _clauses(self, obj) -> list:
        clauses = list()
        for field, choices in [
            ("require_timer_types", Timer.TYPE_CHOICES),
            ("exclude_timer_types", Timer.TYPE_CHOICES),
            ("require_objectives", Timer.OBJECTIVE_CHOICES),
            ("exclude_objectives", Timer.OBJECTIVE_CHOICES),
            ("require_visibility", Timer.VISIBILITY_CHOICES),
            ("exclude_visibility", Timer.VISIBILITY_CHOICES),
        ]:
            if getattr(obj, field):
                text = ", ".join(
                    map(
                        str,
                        [
                            NotificationRule.get_multiselect_display(x, choices)
                            for x in getattr(obj, field)
                        ],
                    )
                )
                clauses.append(f"{make_nice(field)} = {text}")

        for field in [
            "require_corporations",
            "exclude_corporations",
            "require_alliances",
            "exclude_alliances",
        ]:
            if getattr(obj, field).count() > 0:
                text = ", ".join(map(str, getattr(obj, field).all()))
                clauses.append(f"{make_nice(field)} = {text}")

        for field in [
            "is_important",
            "is_opsec",
        ]:
            if getattr(obj, field) != NotificationRule.CLAUSE_ANY:
                text = getattr(obj, f"get_{field}_display")()
                clauses.append(f"{make_nice(field)} = {text}")

        return mark_safe("<br>".join(clauses)) if clauses else None

    def _webhooks(self, obj):
        return list(obj.webhooks.values_list("name", flat=True).order_by("name"))

    filter_horizontal = (
        "require_alliances",
        "exclude_alliances",
        "require_corporations",
        "exclude_corporations",
        "webhooks",
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """overriding this formfield to have sorted lists in the form"""
        if db_field.name in {"require_alliances", "exclude_alliances"}:
            kwargs["queryset"] = EveAllianceInfo.objects.all().order_by(
                Lower("alliance_name")
            )

        elif db_field.name in {"require_corporations", "exclude_corporations"}:
            kwargs["queryset"] = EveCorporationInfo.objects.all().order_by(
                Lower("corporation_name")
            )

        elif db_field.name == "webhooks":
            kwargs["queryset"] = DiscordWebhook.objects.all().order_by(Lower("name"))

        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_select_related = ("timer", "notification_rule")
    list_display = ("notification_date", "timer", "notification_rule", "celery_task_id")
    list_filter = ("notification_rule",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(notification_date__gt=now()).order_by("notification_date")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Timer)
class TimerAdmin(admin.ModelAdmin):
    list_select_related = ("eve_solar_system", "structure_type", "user")
    list_filter = (
        "timer_type",
        ("eve_solar_system", admin.RelatedOnlyFieldListFilter),
        ("structure_type", admin.RelatedOnlyFieldListFilter),
        "objective",
        "owner_name",
        ("user", admin.RelatedOnlyFieldListFilter),
        "is_opsec",
    )
    ordering = ("-date",)
    autocomplete_fields = ["eve_solar_system", "structure_type"]

    """
    def _scheduled_notifications(self, obj):
        return sorted(
            [
                x["notification_date"].strftime(DATETIME_FORMAT)
                for x in ScheduledNotification.objects.filter(
                    timer=obj, notification_date__gt=now()
                ).values("notification_date", "notification_rule_id")
            ]
        )
    """
    actions = ["send_test_notification"]

    def send_test_notification(self, request, queryset):
        for timer in queryset:
            for webhook in DiscordWebhook.objects.filter(is_enabled=True):
                timer.send_notification(webhook=webhook)

            self.message_user(
                request, f"Initiated sending test notification for timer: {timer}"
            )

        for webhook in DiscordWebhook.objects.filter(is_enabled=True):
            tasks.send_messages_for_webhook.delay(webhook.pk)

    send_test_notification.short_description = (
        "Send test notification for this timer to all enabled webhooks"
    )
