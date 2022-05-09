"""Tests for Navigation Highlight"""

from django.urls import reverse
from django_webtest import TestCase

from .testdata.factory import create_user
from .testdata.fixtures import LoadTestDataMixin
from .utils import add_permission_to_user_by_name


class TestNavigationHighlight(LoadTestDataMixin, TestCase):
    """Let's see if we have a highlight in the sidebar navigation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # user
        cls.user_1 = create_user(cls.character_1)
        cls.user_1 = add_permission_to_user_by_name(
            "structuretimers.manage_timer", cls.user_1
        )
        cls.user_1 = add_permission_to_user_by_name(
            "structuretimers.create_timer", cls.user_1
        )

    def test_nav_highlight_for_timer_list(self):
        """test highlight for structuretimers:timer_list"""

        # given
        self.client.force_login(self.user_1)

        # when
        response = self.client.get(reverse("structuretimers:timer_list"))

        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a class="active" href="/structuretimers/">')

    def test_nav_highlight_for_add(self):
        """test highlight for structuretimers:add"""

        # given
        self.client.force_login(self.user_1)

        # when
        response = self.client.get(reverse("structuretimers:add"))

        # then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a class="active" href="/structuretimers/">')
