from .utils import clean_setting

# Will not schedule notifications for timers
# which have elapsed more than x minutes ago
TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS = clean_setting(
    "TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS", 60
)

# Wether notifications for timers are scheduled at all
TIMERBOARD2_NOTIFICATIONS_ENABLED = clean_setting(
    "TIMERBOARD2_NOTIFICATIONS_ENABLED", True
)

# Minimum age in days for a timer to be considered obsolete
# Obsolete timers will automatically be deleted
TIMERBOARD2_TIMERS_OBSOLETE_AFTER_DAYS = clean_setting(
    "TIMERBOARD2_TIMERS_OBSOLETE_AFTER_DAYS", default_value=30, min_value=1
)
