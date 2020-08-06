from django.db import models


class NotificationRuleQuerySet(models.QuerySet):
    def conforms_with_timer(self, timer: object) -> models.QuerySet:
        """returns new queryset based on current queryset, which only contains notification rules that conforms with the given timer"""
        matching_rule_pks = list()
        for notification_rule in self:
            if notification_rule.is_matching_timer(timer):
                matching_rule_pks.append(notification_rule.pk)

        return self.filter(pk__in=matching_rule_pks)


class NotificationRuleManager(models.Manager):
    def get_queryset(self):
        return NotificationRuleQuerySet(self.model, using=self._db)


class TimerQuerySet(models.QuerySet):
    def conforms_with_notification_rule(
        self, notification_rule: object
    ) -> models.QuerySet:
        """returns new queryset based on current queryset, which only contains timers that conform with the given notification rule"""
        matching_timer_pks = list()
        for timer in self:
            if notification_rule.is_matching_timer(timer):
                matching_timer_pks.append(timer.pk)

        return self.filter(pk__in=matching_timer_pks)


class TimerManager(models.Manager):
    def get_queryset(self):
        return TimerQuerySet(self.model, using=self._db)
