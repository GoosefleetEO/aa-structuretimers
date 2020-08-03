from .utils import clean_setting

# do not send notifications for timers which event time is more than
# given minutes in the past.
TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS = clean_setting(
    "TIMERBOARD2_MAX_AGE_FOR_NOTIFICATIONS", 60
)
