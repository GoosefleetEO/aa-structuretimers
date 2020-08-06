from .utils import clean_setting

# Will not sent notifications for timers
# which event time is older than the given minutes
TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS = clean_setting(
    "TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS", 60
)

# Wether sending of notifications are generally enabled
TIMERBOARD2_NOTIFICATIONS_ENABLED = clean_setting(
    "TIMERBOARD2_NOTIFICATIONS_ENABLED", True
)
