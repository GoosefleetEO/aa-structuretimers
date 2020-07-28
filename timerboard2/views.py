from datetime import timedelta
import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.html import format_html, mark_safe
from django.shortcuts import get_object_or_404, render, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from django.views import View
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from allianceauth.eveonline.evelinks import evewho, dotlan

from . import __title__
from .form import TimerForm
from .models import Timer
from .utils import (
    add_no_wrap_html,
    add_bs_label_html,
    create_bs_glyph_html,
    create_bs_button_html,
    create_link_html,
    yesno_str,
    timeuntil_str,
    messages_plus,
)

logger = logging.getLogger(__name__)
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
MAX_HOURS_PASSED = 2


@login_required
@permission_required("timerboard2.basic_access")
def timer_list(request):
    context = {
        "current_time": now().strftime("%Y-%m-%d %H:%M:%S"),
        "max_hours_expired": MAX_HOURS_PASSED,
        "title": __title__,
    }
    return render(request, "timerboard2/timer_list.html", context=context)


def _timers_visible_to_user(user):
    """returns queryset of all timerboard2 visible to the given user"""
    user_ids = list(
        user.character_ownerships.select_related("character").values(
            "character__corporation_id", "character__alliance_id"
        )
    )
    user_corporation_ids = {x["character__corporation_id"] for x in user_ids}
    user_alliance_ids = {x["character__alliance_id"] for x in user_ids}

    timers_qs = Timer.objects.select_related(
        "structure_type", "eve_corp", "eve_alliance"
    )

    if not user.has_perm("timerboard2.view_opsec_timer"):
        timers_qs = timers_qs.exclude(opsec=True)

    timers_qs = (
        timers_qs.filter(visibility=Timer.VISIBILITY_UNRESTRICTED)
        | timers_qs.filter(user=user)
        | timers_qs.filter(
            visibility=Timer.VISIBILITY_CORPORATION,
            eve_corp__corporation_id__in=user_corporation_ids,
        )
        | timers_qs.filter(
            visibility=Timer.VISIBILITY_ALLIANCE,
            eve_alliance__alliance_id__in=user_alliance_ids,
        )
    )
    return timers_qs


@login_required
@permission_required("timerboard2.basic_access")
def timer_list_data(request, tab_name):
    """returns timer list in JSON for AJAX call in timer_list view"""

    timers_qs = _timers_visible_to_user(request.user)

    if tab_name == "current":
        timers_qs = timers_qs.filter(
            eve_time__gte=now() - timedelta(hours=MAX_HOURS_PASSED)
        )
    else:
        timers_qs = timers_qs.filter(eve_time__lt=now())

    data = list()
    for timer in timers_qs:

        # timer
        is_passed = timer.eve_time < now()
        time = timer.eve_time.strftime(DATETIME_FORMAT)
        if is_passed:
            countdown_str = "PASSED"
        else:
            duration = timer.eve_time - now()
            countdown_str = timeuntil_str(duration)

        time += format_html("<br>{}", countdown_str)

        # location
        location = create_link_html(dotlan.solar_system_url(timer.system), timer.system)
        if timer.planet_moon:
            location += format_html("<br>{}", timer.planet_moon)

        # structure & timer type & fitting image
        timer_type = add_bs_label_html(
            timer.get_timer_type_display(), timer.label_type_for_timer_type()
        )
        if timer.structure_type:
            structure_type_icon_url = timer.structure_type.icon_url(size=64)
            structure_type_name = timer.structure_type.name
        else:
            structure_type_icon_url = ""
            structure_type_name = "(unknown)"

        structure = format_html(
            '<div class="flex-container">'
            '<div><img src="{}" width="38"></div>'
            '<div style="text-align: left">'
            "{}&nbsp;<br>"
            "{}"
            "</div>"
            "</div>",
            structure_type_icon_url,
            mark_safe(add_bs_label_html(structure_type_name, "info")),
            timer_type,
        )

        # objective & tags
        tags = list()
        if timer.opsec:
            tags.append(add_bs_label_html("OPSEC", "danger"))
        if timer.visibility != Timer.VISIBILITY_UNRESTRICTED:
            tags.append(add_bs_label_html(timer.get_visibility_display(), "info"))
        if timer.important:
            tags.append(add_bs_label_html("Important", "warning"))

        objective = format_html(
            "{}<br>{}",
            mark_safe(
                add_bs_label_html(
                    timer.get_objective_new_display(), timer.label_type_for_objective()
                )
            ),
            mark_safe(" ".join(tags)),
        )

        # name & owner
        if timer.owner_name:
            owner_name = timer.owner_name
            owner = create_link_html(dotlan.corporation_url(owner_name), owner_name)
        else:
            owner = "-"
            owner_name = ""
        name = format_html("{}<br>{}", timer.details, owner)

        # creator
        if timer.eve_corp:
            corporation_name = timer.eve_corp.corporation_name
        else:
            corporation_name = ""
        creator = format_html(
            "{}<br>{}",
            create_link_html(
                evewho.character_url(timer.eve_character.character_id),
                timer.eve_character.character_name,
            ),
            corporation_name,
        )

        # visibility
        visibility = ""
        if timer.visibility == Timer.VISIBILITY_ALLIANCE and timer.eve_alliance:
            visibility = timer.eve_alliance.alliance_name
        elif timer.visibility == Timer.VISIBILITY_CORPORATION:
            visibility = corporation_name

        # actions
        actions = ""
        disabled_html = ' disabled="disabled">' if not timer.fitting_image_url else ""
        actions += (
            format_html(
                '<a type="button" id="timerboardBtnDetails" class="btn btn-default" '
                'data-toggle="modal" data-target="#modalFitting" '
                'data-timerpk="{}"{}>{}</a>',
                timer.pk,
                disabled_html,
                create_bs_glyph_html("zoom-in"),
            )
            + "&nbsp;"
        )

        if request.user.has_perm("timer_management"):
            actions += (
                create_bs_button_html(
                    reverse("timerboard2:delete", args=(timer.pk,)), "trash", "danger",
                )
                + "&nbsp;"
                + create_bs_button_html(
                    reverse("timerboard2:edit", args=(timer.pk,)), "pencil", "info",
                )
            )

        actions = add_no_wrap_html(actions)

        data.append(
            {
                "id": timer.id,
                "time": time,
                "eve_time": timer.eve_time.isoformat(),
                "location": location,
                "structure_details": structure,
                "name_objective": name,
                "owner": objective,
                "creator": creator,
                "actions": actions,
                "timer_type_name": timer.get_timer_type_display(),
                "objective_name": timer.objective,
                "system_name": timer.system,
                "structure_name": timer.structure,
                "owner_name": owner_name,
                "visibility": visibility,
                "opsec": yesno_str(timer.opsec),
                "is_opsec": timer.opsec,
                "is_passed": is_passed,
                "is_important": timer.important,
            }
        )
    return JsonResponse(data, safe=False)


@login_required
@permission_required("timerboard2.basic_access")
def get_timer_data(request, pk):
    """returns data for a timer"""
    timers_qs = _timers_visible_to_user(request.user)
    timers_qs = timers_qs.filter(pk=pk)
    if timers_qs.exists():
        timer = timers_qs.first()
        data = {
            "display_name": str(timer),
            "structure_display_name": timer.structure_display_name,
            "fitting_image_url": timer.fitting_image_url,
            "notes": timer.structure_display_name,
        }
        return JsonResponse(data, safe=False)
    else:
        return HttpResponseForbidden()


class BaseTimerView(LoginRequiredMixin, PermissionRequiredMixin, View):
    pass


class TimerManagementView(BaseTimerView):
    permission_required = "auth.timer_management"
    index_redirect = "timerboard2:timer_list"
    success_url = reverse_lazy(index_redirect)
    model = Timer
    form_class = TimerForm

    def get_timer(self, timer_id):
        return get_object_or_404(self.model, id=timer_id)


class AddUpdateMixin:
    def get_form_kwargs(self):
        """
        Inject the request user into the kwargs passed to the form
        """
        kwargs = super(AddUpdateMixin, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs


class AddTimerView(TimerManagementView, AddUpdateMixin, CreateView):
    template_name_suffix = "_create_form"

    def form_valid(self, form):
        result = super(AddTimerView, self).form_valid(form)
        timer = self.object
        logger.info(
            "Created new timer in {} at {} by user {}".format(
                timer.system, timer.eve_time, self.request.user
            )
        )
        messages_plus.success(
            self.request,
            _("Added new timer in %(system)s at %(time)s.")
            % {
                "system": timer.system,
                "time": timer.eve_time.strftime(DATETIME_FORMAT),
            },
        )
        return result


class EditTimerView(TimerManagementView, AddUpdateMixin, UpdateView):
    template_name_suffix = "_update_form"

    def form_valid(self, form):
        """
        timer = self.object        
        messages_plus.success(
            self.request, _('Saved changes to the timer: {}.').format(timer)
        )
        """
        return super(EditTimerView, self).form_valid(form)


class RemoveTimerView(TimerManagementView, DeleteView):
    pass
