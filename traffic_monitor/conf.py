from django.conf import settings as django_settings
from django.core.signals import setting_changed


DEFAULTS = {
    'TRAFFIC_MONITOR_INTERFACE_NAMES': None,
    'TRAFFIC_MONITOR_PERMISSION': 'staff',  # superuser, staff, member, all
    'TRAFFIC_MONITOR_TEMPLATE': 'traffic_monitor/show_traffic.html',
    'TRAFFIC_MONITOR_DAILY_ALARM_BYTES': 100 * 1024 * 1024 * 1024,
    'TRAFFIC_MONITOR_MONTHLY_ALARM_BYTES': 800 * 1024 * 1024 * 1024,
    'TRAFFIC_MONITOR_EMAIL_FROM': django_settings.DEFAULT_FROM_EMAIL,
    'TRAFFIC_MONITOR_EMAIL_TO': [django_settings.DEFAULT_FROM_EMAIL],
    'TRAFFIC_MONITOR_ALARM_SEND_EMAIL': True,
    'TRAFFIC_MONITOR_ALARM_EMAIL_SUBJECT': 'Traffic limit alert',
    'TRAFFIC_MONITOR_ALARM_BYTES_THRESHOLD': 10 * 1024 * 1024 * 1024,
}


class Settings(object):
    def __init__(self):
        super(Settings, self).__setattr__('_settings', {})
        self.defaults = DEFAULTS
        for key, default in DEFAULTS.items():
            self._settings[key] = getattr(django_settings, key, default)

        self.last_total_bytes = 0

    def reload(self):
        self.__init__()

    def __getattr__(self, attr):
        """Get attr"""
        if attr not in DEFAULTS:
            raise AttributeError("Invalid setting: '%s'" % attr)
        return self._settings[attr]

    def get_last_total_bytes(self):
        return self.last_total_bytes

    def set_last_total_bytes(self, total_bytes):
        self.last_total_bytes = total_bytes


settings = Settings()


def reload_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting in settings.DEFAULTS:
        settings.reload()


setting_changed.connect(reload_settings)
