from datetime import timedelta
import logging

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.utils.html import format_html, mark_safe
from django.shortcuts import render, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from django.views import View
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from allianceauth.eveonline.evelinks import evewho, dotlan

from eveuniverse.models import EveSolarSystem, EveType

from . import __title__
from .app_settings import (
    STRUCTURETIMERS_DEFAULT_PAGE_LENGTH,
    STRUCTURETIMERS_PAGING_ENABLED,
)
from .forms import TimerForm
from .models import Timer
from .utils import (
    add_no_wrap_html,
    add_bs_label_html,
    create_fa_button_html,
    create_link_html,
    yesno_str,
    timeuntil_str,
    messages_plus,
)

logger = logging.getLogger(__name__)
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
MAX_HOURS_PASSED = 2


@login_required
@permission_required("structuretimers.basic_access")
def timer_list(request):
    context = {
        "current_time": now().strftime("%Y-%m-%d %H:%M:%S"),
        "max_hours_expired": MAX_HOURS_PASSED,
        "title": __title__,
        "data_tables_page_length": STRUCTURETIMERS_DEFAULT_PAGE_LENGTH,
        "data_tables_paging": STRUCTURETIMERS_PAGING_ENABLED,
    }
    return render(request, "structuretimers/timer_list.html", context=context)


@login_required
@permission_required("structuretimers.basic_access")
def timer_list_data(request, tab_name):
    """returns timer list in JSON for AJAX call in timer_list view"""

    timers_qs = Timer.objects.all().visible_to_user(request.user)

    if tab_name == "current":
        timers_qs = timers_qs.filter(
            date__gte=now() - timedelta(hours=MAX_HOURS_PASSED)
        )
    else:
        timers_qs = timers_qs.filter(date__lt=now())

    timers_qs = timers_qs.select_related(
        "eve_solar_system__eve_constellation__eve_region",
        "structure_type",
        "eve_character",
        "eve_corporation",
        "eve_alliance",
    )
    data = list()
    for timer in timers_qs:

        # timer
        is_passed = timer.date < now()
        time = timer.date.strftime(DATETIME_FORMAT)
        if is_passed:
            countdown_str = "ELAPSED"
        else:
            duration = timer.date - now()
            countdown_str = timeuntil_str(duration)

        time += format_html("<br>{}", countdown_str)

        # location
        location = create_link_html(
            dotlan.solar_system_url(timer.eve_solar_system.name),
            timer.eve_solar_system.name,
        )
        if timer.location_details:
            location += format_html("<br><em>{}</em>", timer.location_details)

        location += format_html(
            "<br>{}", timer.eve_solar_system.eve_constellation.eve_region.name
        )

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
            '  <div style="padding-top: 4px;"><img src="{}" width="40"></div>'
            '  <div style="text-align: left;">'
            "    {}&nbsp;<br>"
            "    {}"
            "  </div>"
            "</div>",
            structure_type_icon_url,
            mark_safe(add_bs_label_html(structure_type_name, "info")),
            timer_type,
        )

        # objective & tags
        tags = list()
        is_restricted = False
        if timer.is_opsec:
            tags.append(add_bs_label_html("OPSEC", "danger"))
            is_restricted = True

        if timer.visibility != Timer.VISIBILITY_UNRESTRICTED:
            tags.append(add_bs_label_html(timer.get_visibility_display(), "info"))
            is_restricted = True

        if timer.is_important:
            tags.append(add_bs_label_html("Important", "warning"))

        objective = format_html(
            "{}<br>{}",
            mark_safe(
                add_bs_label_html(
                    timer.get_objective_display(), timer.label_type_for_objective()
                )
            ),
            mark_safe(" ".join(tags)),
        )

        # name & owner
        if timer.owner_name:
            owner_name = timer.owner_name
            owner = owner_name
        else:
            owner = "-"
            owner_name = ""

        structure_name = timer.structure_name if timer.structure_name else "-"
        name = format_html("{}<br>{}", structure_name, owner)

        # creator
        if timer.eve_corporation:
            corporation_name = timer.eve_corporation.corporation_name
        else:
            corporation_name = "-"

        if timer.eve_character:
            creator = format_html(
                "{}<br>{}",
                create_link_html(
                    evewho.character_url(timer.eve_character.character_id),
                    timer.eve_character.character_name,
                ),
                corporation_name,
            )
        elif corporation_name:
            creator = corporation_name
        else:
            creator = "-"

        # visibility
        visibility = ""
        if timer.visibility == Timer.VISIBILITY_ALLIANCE and timer.eve_alliance:
            visibility = timer.eve_alliance.alliance_name
        elif timer.visibility == Timer.VISIBILITY_CORPORATION:
            visibility = corporation_name

        # actions
        actions = ""

        if timer.details_image_url or timer.details_notes:
            disabled_html = ""
            button_type = "primary"
            data_toggle = 'data-toggle="modal" data-target="#modalTimerDetails" '
            title = "Show details of this timer"
        else:
            button_type = "default"
            disabled_html = ' disabled="disabled"'
            data_toggle = ""
            title = "No details available"

        actions += (
            format_html(
                '<a type="button" id="timerboardBtnDetails" '
                f'class="btn btn-{button_type}" title="{title}"'
                f"{data_toggle}"
                f'data-timerpk="{timer.pk}"{disabled_html}>'
                '<i class="fas fa-search-plus"></i></a>'
            )
            + "&nbsp;"
        )

        if request.user.has_perm("structuretimers.manage_timer"):
            actions += (
                create_fa_button_html(
                    reverse("structuretimers:delete", args=(timer.pk,)),
                    "far fa-trash-alt",
                    "danger",
                    "Delete this timer",
                )
                + "&nbsp;"
            )

        if timer.user_can_edit(request.user):
            actions += create_fa_button_html(
                reverse("structuretimers:edit", args=(timer.pk,)),
                "far fa-edit",
                "warning",
                "Edit this timer",
            )

        actions = add_no_wrap_html(actions)

        data.append(
            {
                "id": timer.id,
                "time": time,
                "date": timer.date.isoformat(),
                "location": location,
                "structure_details": structure,
                "name_objective": name,
                "owner": objective,
                "creator": creator,
                "actions": actions,
                "timer_type_name": timer.get_timer_type_display(),
                "objective_name": timer.get_objective_display(),
                "system_name": timer.eve_solar_system.name,
                "region_name": timer.eve_solar_system.eve_constellation.eve_region.name,
                "structure_type_name": timer.structure_type.name,
                "owner_name": owner_name,
                "visibility": visibility,
                "opsec_str": yesno_str(timer.is_opsec),
                "is_opsec": timer.is_opsec,
                "is_passed": is_passed,
                "is_important": timer.is_important,
                "is_restricted": is_restricted,
            }
        )
    return JsonResponse(data, safe=False)


@login_required
@permission_required("structuretimers.basic_access")
def get_timer_data(request, pk):
    """returns data for a timer"""
    timers_qs = Timer.objects.filter(pk=pk).visible_to_user(request.user)
    if timers_qs.exists():
        timer = timers_qs.first()
        data = {
            "display_name": str(timer),
            "structure_display_name": timer.structure_display_name,
            "date": timer.date.strftime(DATETIME_FORMAT),
            "details_image_url": timer.details_image_url
            if timer.details_image_url
            else "",
            "notes": timer.details_notes if timer.details_notes else "",
        }
        return JsonResponse(data, safe=False)
    else:
        return HttpResponseForbidden()


class BaseTimerView(LoginRequiredMixin, PermissionRequiredMixin, View):
    pass


class TimerManagementView(BaseTimerView):
    index_redirect = "structuretimers:timer_list"
    success_url = reverse_lazy(index_redirect)
    model = Timer
    form_class = TimerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Structure Timer"
        return context


class AddUpdateMixin:
    def get_form_kwargs(self):
        """
        Inject the request user into the kwargs passed to the form
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs


class AddTimerView(TimerManagementView, AddUpdateMixin, CreateView):
    permission_required = "structuretimers.create_timer"
    template_name_suffix = "_create_form"

    def form_valid(self, form):
        result = super().form_valid(form)
        timer = self.object
        logger.info(
            "Created new timer in %s at %s by user %s",
            timer.eve_solar_system,
            timer.date,
            self.request.user,
        )
        messages_plus.success(
            self.request,
            _("Added new timer for %(type)s in %(system)s at %(time)s.")
            % {
                "type": timer.structure_type.name,
                "system": timer.eve_solar_system.name,
                "time": timer.date.strftime(DATETIME_FORMAT),
            },
        )
        return result


class EditTimerView(TimerManagementView, AddUpdateMixin, UpdateView):
    permission_required = "structuretimers.basic_access"
    template_name_suffix = "_update_form"

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if (
            not self.object.user_can_edit(self.request.user)
            or not Timer.objects.filter(pk=self.object.pk)
            .visible_to_user(self.request.user)
            .exists()
        ):
            raise PermissionDenied()

        return response

    """
    def form_valid(self, form):        
        timer = self.object        
        messages_plus.success(
            self.request, _('Saved changes to the timer: {}.').format(timer)
        )        
        return super().form_valid(form)
    """


class RemoveTimerView(TimerManagementView, DeleteView):
    permission_required = "structuretimers.manage_timer"


@login_required
@permission_required("structuretimers.basic_access")
def select2_solar_systems(request):
    term = request.GET.get("term")
    if term:
        results = [
            {"id": row["id"], "text": row["name"]}
            for row in EveSolarSystem.objects.filter(name__istartswith=term).values(
                "id", "name"
            )
        ]
    else:
        results = None

    return JsonResponse({"results": results}, safe=False)


@login_required
@permission_required("structuretimers.basic_access")
def select2_structure_types(request):
    term = request.GET.get("term")
    if term:
        types_qs = (
            EveType.objects.filter(eve_group__eve_category_id__in=[65], published=True)
            | EveType.objects.filter(eve_group_id=365, published=True)
            | EveType.objects.filter(id=2233)
        )
        types_qs = (
            types_qs.select_related("eve_category", "eve_category__eve_group")
            .distinct()
            .filter(name__icontains=term)
        )
        results = [
            {"id": row["id"], "text": row["name"]}
            for row in types_qs.values("id", "name")
        ]
    else:
        results = None

    return JsonResponse({"results": results}, safe=False)
