from unittest.mock import patch

from requests.exceptions import ConnectionError as NewConnectionError
from requests.exceptions import HTTPError

from app_utils.testing import NoSocketsTestCase

from ..forms import TimerForm
from ..models import Timer
from . import LoadTestDataMixin
from .testdata import test_image_filename

FORMS_PATH = "structuretimers.forms"


def bytes_from_file(filename, chunksize=8192):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                for b in chunk:
                    yield b
            else:
                break


def create_form_data(**kwargs):
    form_data = {
        "eve_solar_system_2": TestTimerForm.system_abune.id,
        "structure_type_2": TestTimerForm.type_astrahus.id,
        "timer_type": Timer.Type.NONE,
        "objective": Timer.Objective.UNDEFINED,
        "visibility": Timer.Visibility.UNRESTRICTED,
    }
    if kwargs:
        form_data.update(kwargs)
    return form_data


class TestTimerForm(LoadTestDataMixin, NoSocketsTestCase):
    def test_should_accept_normal_timer(self):
        # given
        form_data = create_form_data(days_left=0, hours_left=3, minutes_left=30)
        form = TimerForm(data=form_data)
        # when / then
        self.assertTrue(form.is_valid())

    def test_should_not_accept_timer_without_solar_system(self):
        # given
        form_data = create_form_data(days_left=0, hours_left=3, minutes_left=30)
        del form_data["eve_solar_system_2"]
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    def test_should_not_accept_timer_without_structure_type(self):
        # given
        form_data = create_form_data(days_left=0, hours_left=3, minutes_left=30)
        del form_data["structure_type_2"]
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    def test_should_not_accept_timer_without_days(self):
        # given
        form_data = create_form_data(hours_left=3, minutes_left=30)
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    def test_should_not_accept_timer_without_hours(self):
        # given
        form_data = create_form_data(days_left=3, minutes_left=30)
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    def test_should_not_accept_timer_without_minutes(self):
        # given
        form_data = create_form_data(days_left=3, hours_left=4)
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    def test_should_not_accept_invalid_days(self):
        # given
        form_data = create_form_data(days_left=-1, hours_left=3, minutes_left=30)
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    def test_should_accept_target_timer_without_date(self):
        # given
        form_data = create_form_data(timer_type=Timer.Type.PRELIMINARY)
        form = TimerForm(data=form_data)
        # when / then
        self.assertTrue(form.is_valid())

    def test_should_not_accept_moon_mining_type_for_non_mining_structures(self):
        # given
        form_data = create_form_data(
            timer_type=Timer.Type.MOONMINING,
            structure_type_2=self.type_astrahus.id,
            days_left=0,
            hours_left=3,
            minutes_left=30,
        )
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    @patch(FORMS_PATH + ".requests.get", spec=True)
    def test_should_create_timer_with_valid_details_image(self, mock_get):
        # given
        image_file = bytearray(bytes_from_file(test_image_filename()))
        mock_get.return_value.content = image_file
        form_data = create_form_data(
            days_left=0,
            hours_left=3,
            minutes_left=30,
            details_image_url="http://www.example.com/image.png",
        )
        form = TimerForm(data=form_data)
        # when / then
        self.assertTrue(form.is_valid())

    @patch(FORMS_PATH + ".requests.get", spec=True)
    def test_should_not_allow_invalid_link_for_detail_images(self, mock_get):
        # given
        image_file = bytearray(bytes_from_file(test_image_filename()))
        mock_get.return_value.content = image_file
        form_data = create_form_data(
            days_left=0,
            hours_left=3,
            minutes_left=30,
            details_image_url="invalid-url",
        )
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    @patch(FORMS_PATH + ".requests.get", spec=True)
    def test_should_show_error_when_image_can_not_be_loaded_1(self, mock_get):
        # given
        mock_get.side_effect = NewConnectionError
        form_data = create_form_data(
            days_left=0,
            hours_left=3,
            minutes_left=30,
            details_image_url="http://www.example.com/image.png",
        )
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())

    @patch(FORMS_PATH + ".requests.get", spec=True)
    def test_should_show_error_when_image_can_not_be_loaded_2(self, mock_get):
        # given
        mock_get.side_effect = HTTPError
        form_data = create_form_data(
            days_left=0,
            hours_left=3,
            minutes_left=30,
            details_image_url="http://www.example.com/image.png",
        )
        form = TimerForm(data=form_data)
        # when / then
        self.assertFalse(form.is_valid())
