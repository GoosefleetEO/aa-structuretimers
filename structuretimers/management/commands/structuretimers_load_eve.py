import logging
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ... import __title__
from ...constants import (
    EVE_CATEGORY_ID_STRUCTURE,
    EVE_GROUP_ID_CONTROL_TOWER,
    EVE_GROUP_ID_MOBILE_DEPOT,
    EVE_TYPE_ID_CUSTOMS_OFFICE,
    EVE_TYPE_ID_TCU,
    EVE_TYPE_ID_IHUB,
)
from ...utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)


class Command(BaseCommand):
    help = "Preloads data required for this app from ESI"

    def handle(self, *args, **options):
        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            str(EVE_CATEGORY_ID_STRUCTURE),
            "--group_id",
            str(EVE_GROUP_ID_CONTROL_TOWER),
            "--group_id",
            str(EVE_GROUP_ID_MOBILE_DEPOT),
            "--type_id",
            str(EVE_TYPE_ID_CUSTOMS_OFFICE),
            "--type_id",
            str(EVE_TYPE_ID_TCU),
            "--type_id",
            str(EVE_TYPE_ID_IHUB),
        )
