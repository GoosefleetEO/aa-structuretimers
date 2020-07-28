import logging
import datetime

from django import forms
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

from eveuniverse.models import EveGroup

from .models import Timer

logger = logging.getLogger(__name__)


def generate_structure_choices():
    groups_qs = (
        EveGroup.objects.filter(
            eve_category_id__in=[65], published=True, eve_types__published=True
        )
        | EveGroup.objects.filter(id=365, eve_types__published=True)
        | EveGroup.objects.filter(eve_types__id=2233)
    )
    groups_qs = groups_qs.select_related("eve_category").distinct()
    return [
        (group.name, [(x.id, x.name) for x in group.eve_types.order_by("name")],)
        for group in groups_qs.order_by("name")
    ]


class TimerForm(forms.ModelForm):
    class Meta:
        model = Timer
        fields = (
            "system",
            "planet_moon",
            "structure_type_2",
            "timer_type",
            "details",
            "owner_name",
            "objective_new",
            "days_left",
            "hours_left",
            "minutes_left",
            "fitting_image_url",
            "visibility",
            "opsec",
            "important",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        if "instance" in kwargs and kwargs["instance"] is not None:
            # Do conversion from db datetime to days/hours/minutes
            # for appropriate fields
            current_time = timezone.now()
            td = kwargs["instance"].eve_time - current_time
            initial = kwargs.pop("initial", dict())
            if "days_left" not in initial:
                initial.update({"days_left": td.days})
            if "hours_left" not in initial:
                initial.update({"hours_left": td.seconds // 3600})
            if "minutes_left" not in initial:
                initial.update({"minutes_left": td.seconds // 60 % 60})
            initial.update({"structure_type_2": kwargs["instance"].structure_type_id})
            kwargs.update({"initial": initial})
        super(TimerForm, self).__init__(*args, **kwargs)

    structure_type_2 = forms.ChoiceField(
        label=Timer._meta.get_field("structure_type").verbose_name.capitalize(),
        choices=generate_structure_choices,
        help_text=Timer._meta.get_field("structure_type").help_text,
    )

    days_left = forms.IntegerField(
        required=True,
        initial=0,
        label=_("Days Remaining"),
        validators=[MinValueValidator(0)],
    )
    hours_left = forms.IntegerField(
        required=True,
        initial=0,
        label=_("Hours Remaining"),
        validators=[MinValueValidator(0), MaxValueValidator(23)],
    )
    minutes_left = forms.IntegerField(
        required=True,
        initial=0,
        label=_("Minutes Remaining"),
        validators=[MinValueValidator(0), MaxValueValidator(59)],
    )

    def save(self, commit=True):
        timer = super(TimerForm, self).save(commit=False)

        # Get character
        character = self.user.profile.main_character
        corporation = character.corporation
        logger.debug(
            "Determined timer save request on behalf "
            "of character {} corporation {}".format(character, corporation)
        )
        # calculate future time
        future_time = datetime.timedelta(
            days=self.cleaned_data["days_left"],
            hours=self.cleaned_data["hours_left"],
            minutes=self.cleaned_data["minutes_left"],
        )
        current_time = timezone.now()
        eve_time = current_time + future_time
        logger.debug(
            "Determined timer eve time is %s - current time %s, "
            "adding %s" % (eve_time, current_time, future_time)
        )

        # get structure type
        structure_type_id = self.cleaned_data["structure_type_2"]

        timer.structure_type_id = structure_type_id
        timer.eve_time = eve_time
        timer.eve_character = character
        timer.eve_corp = corporation
        timer.user = self.user
        if commit:
            timer.save()
        return timer
