from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView

from . import conf
from . import models
from . import tools


class TrafficSummaryView(UserPassesTestMixin, TemplateView):
    http_method_names = ['get']
    template_name = conf.settings.TRAFFIC_MONITOR_TEMPLATE

    def test_func(self):
        permission = conf.settings.TRAFFIC_MONITOR_PERMISSION
        if permission == 'superuser':
            return self.request.user.is_superuser
        elif permission == 'staff':
            return self.request.user.is_staff
        elif permission == 'member':
            return self.request.user.is_authenticated
        elif permission == 'all':
            return True
        else:
            return False

    def get_context_data(self, **kwargs):
        context = super(TrafficSummaryView, self).get_context_data(**kwargs)

        traffics = models.Traffic.objects.this_month()
        month_total_bytes = 0
        month_data = []

        for data in traffics:
            daily_data = {
                'date': data.date,
                'rx': tools.print_unit(data.rx_bytes),
                'tx': tools.print_unit(data.tx_bytes),
                'total': tools.print_unit(data.total())
            }
            month_data.append(daily_data)
            month_total_bytes += data.rx_bytes + data.tx_bytes

        today_traffic = models.Traffic.objects.today()
        if today_traffic:
            context['today_total'] = tools.print_unit(today_traffic.total())
            context['last_updated_at'] = today_traffic.updated_at
        else:
            context['today_total'] = 0
            context['last_updated_at'] = 'NaN'

        context['month_data'] = month_data
        context['month_total'] = tools.print_unit(month_total_bytes)

        return context


class TrafficRefreshView(TrafficSummaryView):
    def get(self, request, *args, **kwargs):
        tools.read_bytes()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
