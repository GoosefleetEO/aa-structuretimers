from celery import shared_task

from django.contrib.auth.models import User

from allianceauth.notifications import notify
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

from . import __title__
from .models import DiscordWebhook, NotificationRule
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@shared_task(base=QueueOnce)
def send_messages_for_webhook(webhook_pk: int) -> None:
    """sends all currently queued messages for given webhook to Discord"""
    try:
        webhook = DiscordWebhook.objects.get(pk=webhook_pk)
    except DiscordWebhook.DoesNotExist:
        logger.error("DiscordWebhook with pk = %s does not exist", webhook_pk)
    else:
        if not webhook.is_enabled:
            logger.info(
                "Tracker %s: DiscordWebhook disabled - skipping sending", webhook
            )
            return

        logger.info("Started sending messages to webhook %s", webhook)
        webhook.send_queued_messages()
        logger.info("Completed sending messages to webhook %s", webhook)


@shared_task
def process_notification_rules(rule_pk: int) -> None:
    try:
        notification_rule = NotificationRule.objects.get(pk=rule_pk)
    except NotificationRule.DoesNotExist:
        logger.error("NotificationRule with pk = %s does not exist", rule_pk)
    else:
        logger.info("Processing notification rule %s", rule_pk)
        notification_rule.process_timers()


@shared_task
def process_all():
    for rule in NotificationRule.objects.filter(is_enabled=True):
        process_notification_rules.delay(rule.pk)


@shared_task
def send_test_message_to_webhook(webhook_pk: int, user_pk: int = None) -> None:
    """send a test message to given webhook. 
    Optional inform user about result if user ok is given
    """
    try:
        webhook = DiscordWebhook.objects.get(pk=webhook_pk)
    except DiscordWebhook.DoesNotExist:
        logger.error("DiscordWebhook with pk = %s does not exist", webhook_pk)
    else:
        logger.info("Sending test message to webhook %s", webhook)
        error_text, success = webhook.send_test_message()

        if user_pk:
            message = (
                f"Error text: {error_text}\nCheck log files for details."
                if not success
                else "No errors"
            )
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                logger.warning("User with pk = %s does not exist", user_pk)
            else:
                level = "success" if success else "error"
                notify(
                    user=user,
                    title=(
                        f"{__title__}: Result of test message to webhook {webhook}: "
                        f"{level.upper()}"
                    ),
                    message=message,
                    level=level,
                )
