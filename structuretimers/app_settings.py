from app_utils.django import clean_setting

# Will not schedule notifications for timers
# which have elapsed more than x minutes ago
STRUCTURETIMERS_MAX_AGE_FOR_NOTIFICATIONS = clean_setting(
    "STRUCTURETIMERS_MAX_AGE_FOR_NOTIFICATIONS", 60
)

# Wether notifications for timers are scheduled at all
STRUCTURETIMERS_NOTIFICATIONS_ENABLED = clean_setting(
    "STRUCTURETIMERS_NOTIFICATIONS_ENABLED", True
)

# Minimum age in days for a timer to be considered obsolete
# Obsolete timers will automatically be deleted
STRUCTURETIMERS_TIMERS_OBSOLETE_AFTER_DAYS = clean_setting(
    "STRUCTURETIMERS_TIMERS_OBSOLETE_AFTER_DAYS", default_value=30, min_value=1
)

# Default page size for timerboard.
# Must be an integer value from the current options as seen in the app.
STRUCTURETIMERS_DEFAULT_PAGE_LENGTH = clean_setting(
    "STRUCTURETIMERS_DEFAULT_PAGE_LENGTH", 10
)

# Wether paging is enabled on the timerboard
STRUCTURETIMERS_PAGING_ENABLED = clean_setting("STRUCTURETIMERS_PAGING_ENABLED", True)

# Eve ID of the home solar system. Distances will be calculated from that system.
STRUCTURETIMERS_HOME_SYSTEM_ID = clean_setting(
    "STRUCTURETIMERS_HOME_SYSTEM_ID", default_value=None, required_type=int
)
