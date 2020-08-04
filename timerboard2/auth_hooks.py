from django.utils.translation import ugettext_lazy as _

from allianceauth.services.hooks import MenuItemHook, UrlHook
from allianceauth import hooks

from . import urls


class TimersMenuItem(MenuItemHook):
    """ This class ensures only authorized users will see the menu entry """

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Timerboard"),
            "far fa-calendar-times",
            "timerboard2:timer_list",
            navactive=["timerboard2:timer_list"],
        )

    def render(self, request):
        if request.user.has_perm("timerboard2.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    return TimersMenuItem()


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "timerboard2", r"^timerboard/")
