from django.conf.urls import url

from . import views

app_name = "structuretimers"

urlpatterns = [
    url(r"^$", views.timer_list, name="timer_list"),
    url(r"^add/$", views.AddTimerView.as_view(), name="add"),
    url(r"^remove/(?P<pk>\w+)$", views.RemoveTimerView.as_view(), name="delete"),
    url(r"^edit/(?P<pk>\w+)$", views.EditTimerView.as_view(), name="edit"),
    url(
        r"^list_data/(?P<tab_name>\w+)$", views.timer_list_data, name="timer_list_data"
    ),
    url(r"^get_timer_data/(?P<pk>\w+)$", views.get_timer_data, name="get_timer_data"),
    url(
        r"^select2_solar_systems/$",
        views.select2_solar_systems,
        name="select2_solar_systems",
    ),
    url(
        r"^select2_structure_types/$",
        views.select2_structure_types,
        name="select2_structure_types",
    ),
]
