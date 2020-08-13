import logging
import datetime

from django import forms
from django.utils import timezone
from django.utils.html import mark_safe
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

from .models import Timer

logger = logging.getLogger(__name__)


class TimerForm(forms.ModelForm):
    class Meta:
        model = Timer
        fields = (
            "eve_solar_system_2",
            "location_details",
            "structure_type_2",
            "timer_type",
            "structure_name",
            "owner_name",
            "objective",
            "days_left",
            "hours_left",
            "minutes_left",
            "details_image_url",
            "details_notes",
            "visibility",
            "is_opsec",
            "is_important",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        if "instance" in kwargs and kwargs["instance"] is not None:
            # Do conversion from db datetime to days/hours/minutes
            # for appropriate fields
            my_instance = kwargs["instance"]
            current_time = timezone.now()
            td = my_instance.date - current_time
            initial = kwargs.pop("initial", dict())
            if "days_left" not in initial:
                initial.update({"days_left": td.days})
            if "hours_left" not in initial:
                initial.update({"hours_left": td.seconds // 3600})
            if "minutes_left" not in initial:
                initial.update({"minutes_left": td.seconds // 60 % 60})

            kwargs.update({"initial": initial})
            self.is_new = False
        else:
            my_instance = None
            self.is_new = True

        super().__init__(*args, **kwargs)

        if my_instance:
            self.fields["eve_solar_system_2"].widget.choices = [
                (
                    str(my_instance.eve_solar_system_id),
                    my_instance.eve_solar_system.name,
                )
            ]
            self.fields["structure_type_2"].widget.choices = [
                (str(my_instance.structure_type_id), my_instance.structure_type.name,)
            ]

    asterisk_html = '<i class="fas fa-asterisk"></i>'
    eve_solar_system_2 = forms.CharField(
        required=True,
        label=_(mark_safe(f"Solar System {asterisk_html}")),
        widget=forms.Select(attrs={"class": "select2-solar-systems"}),
    )
    structure_type_2 = forms.CharField(
        required=True,
        label=_(mark_safe(f"Structure Type {asterisk_html}")),
        widget=forms.Select(attrs={"class": "select2-structure-types"}),
    )
    objective = forms.ChoiceField(
        initial=Timer.OBJECTIVE_UNDEFINED,
        choices=Timer.OBJECTIVE_CHOICES,
        widget=forms.Select(attrs={"class": "select2-render"}),
    )
    timer_type = forms.ChoiceField(
        choices=Timer.TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "select2-render"}),
    )
    visibility = forms.ChoiceField(
        choices=Timer.VISIBILITY_CHOICES,
        widget=forms.Select(attrs={"class": "select2-render"}),
    )
    days_left = forms.IntegerField(
        required=True,
        label=_(mark_safe(f"Days Remaining {asterisk_html}")),
        validators=[MinValueValidator(0)],
    )
    hours_left = forms.IntegerField(
        required=True,
        label=_(mark_safe(f"Hours Remaining {asterisk_html}")),
        validators=[MinValueValidator(0), MaxValueValidator(23)],
    )
    minutes_left = forms.IntegerField(
        required=True,
        label=_(mark_safe(f"Minutes Remaining {asterisk_html}")),
        validators=[MinValueValidator(0), MaxValueValidator(59)],
    )

    def save(self, commit=True):
        timer = super(TimerForm, self).save(commit=False)

        # character / corporation / alliance
        if self.is_new:
            character = self.user.profile.main_character
            try:
                alliance = character.alliance
            except EveAllianceInfo.DoesNotExist:
                alliance = EveAllianceInfo.objects.create_alliance(
                    character.alliance_id
                )

            try:
                corporation = character.corporation
            except EveCorporationInfo.DoesNotExist:
                corporation = EveCorporationInfo.objects.create_corporation(
                    character.corporation_id
                )

            logger.debug(
                "Determined timer save request is on behalf of character %s corporation %s",
                character,
                corporation,
            )
            timer.eve_character = character
            timer.eve_corporation = corporation
            timer.eve_alliance = alliance
            timer.user = self.user

        # calculate future time
        future_time = datetime.timedelta(
            days=self.cleaned_data["days_left"],
            hours=self.cleaned_data["hours_left"],
            minutes=self.cleaned_data["minutes_left"],
        )
        current_time = timezone.now()
        date = current_time + future_time
        logger.debug(
            "Determined timer eve time is %s - current time %s, adding %s",
            date,
            current_time,
            future_time,
        )
        timer.date = date

        # structure type
        timer.structure_type_id = self.cleaned_data["structure_type_2"]
        timer.eve_solar_system_id = self.cleaned_data["eve_solar_system_2"]

        if commit:
            timer.save()
        return timer
