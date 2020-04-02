from django.conf.urls import url

from . import views

app_name = 'traffic_monitor'

urlpatterns = [
    url(
        r'^$',
        views.TrafficSummaryView.as_view(),
        name='show_traffic'
    ),
    url(
        r'^refresh/',
        views.TrafficRefreshView.as_view(),
        name='refresh_traffic'
    ),
]
