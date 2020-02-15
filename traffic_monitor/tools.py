import os
import platform

from django.conf import settings
from django.db.models import F, Sum
from django.utils import timezone

from . import conf
from . import models
from .email import EmailHelper


KILOBYTE = 1024
MEGABYTE = KILOBYTE * 1024
GIGABYTE = MEGABYTE * 1024
TERABYTE = GIGABYTE * 1024
PETABYTE = TERABYTE * 1024
EXABYTE = PETABYTE * 1024
ZETTABYTE = EXABYTE * 1024
YOTTABYTE = ZETTABYTE * 1024

SKIP = True
DO_NOT_SKIP = False


def print_unit(x_bytes):
    if x_bytes >= YOTTABYTE:
        return '%.2f Y' % (x_bytes / YOTTABYTE)
    elif x_bytes >= ZETTABYTE:
        return '%.2f Z' % (x_bytes / ZETTABYTE)
    elif x_bytes >= EXABYTE:
        return '%.2f E' % (x_bytes / EXABYTE)
    elif x_bytes >= PETABYTE:
        return '%.2f P' % (x_bytes / PETABYTE)
    elif x_bytes >= TERABYTE:
        return '%.2f T' % (x_bytes / TERABYTE)
    elif x_bytes >= GIGABYTE:
        return '%.2f G' % (x_bytes / GIGABYTE)
    elif x_bytes >= MEGABYTE:
        return '%.2f M' % (x_bytes / MEGABYTE)
    else:
        return '%.2f K' % (x_bytes / KILOBYTE)


def skip_alarm(total_bytes):
    if not conf.settings.TRAFFIC_MONITOR_ALARM_SEND_EMAIL:
        return SKIP

    last_total_bytes = conf.settings.get_last_total_bytes()
    bytes_threshold = conf.settings.TRAFFIC_MONITOR_ALARM_BYTES_THRESHOLD

    if total_bytes > last_total_bytes + bytes_threshold:
        return DO_NOT_SKIP

    return SKIP


def send_email_alarm(today_total, month_total):
    subject = conf.settings.TRAFFIC_MONITOR_ALARM_EMAIL_SUBJECT

    EmailHelper.send(
        subject=subject,
        body='traffic_monitor/alarm.html',
        html_body='traffic_monitor/alarm.html',
        context={
            'subject': subject,
            'alert_at': timezone.now(),
            'today_total': print_unit(today_total),
            'month_total': print_unit(month_total),
        }
    )

    conf.settings.set_last_total_bytes(today_total)


def check_traffic_limit(today_total):
    if skip_alarm(today_total):
        return

    daily_limit = conf.settings.TRAFFIC_MONITOR_DAILY_ALARM_BYTES
    monthly_limit = conf.settings.TRAFFIC_MONITOR_MONTHLY_ALARM_BYTES
    code_yellow = False

    if daily_limit > 0:
        if today_total > daily_limit:
            code_yellow = True

    month_total = 0
    if monthly_limit > 0:
        month_total = models.Traffic.objects.this_month().aggregate(
            total=Sum(F('rx_bytes') + F('tx_bytes'))
        )['total']
        if month_total > monthly_limit:
            code_yellow = True

    if code_yellow:
        send_email_alarm(today_total, month_total)


def read_bytes():
    interfaces = conf.settings.TRAFFIC_MONITOR_INTERFACE_NAMES
    if not interfaces:
        raise AttributeError("Interfaces must be presented.")

    rx_bytes = tx_bytes = 0

    system = platform.system()
    if system == 'Linux':
        for interface in interfaces.split(','):
            path = '/sys/class/net/%s/statistics/' % interface
            try:
                with open(os.path.join(path, "rx_bytes")) as f:
                    rx_bytes += int(f.read())
                with open(os.path.join(path, "tx_bytes")) as f:
                    tx_bytes += int(f.read())
            except IOError:
                print('Failed to open file from %s' % path)
    elif system == 'Darwin' and settings.DEBUG:
        """
        Test code

        For MacOS local testing. DO NOT RUN in real server
        """
        if hasattr(settings, 'BASE_DIR'):
            base_dir = settings.BASE_DIR
        else:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )

        for interface in interfaces.split(','):
            path = os.path.join(base_dir, ('.net/%s/' % interface))
            try:
                with open(os.path.join(path, "rx_bytes")) as f:
                    rx_bytes += int(f.read())
                with open(os.path.join(path, "tx_bytes")) as f:
                    tx_bytes += int(f.read())
            except IOError:
                print('Failed to open file from %s' % path)
    else:
        raise NotImplementedError("%s is not supported." % system)

    if not models.Traffic.objects.exists():
        models.Traffic.objects.create_init(
            interface=interfaces,
            rx_bytes=rx_bytes,
            tx_bytes=tx_bytes
        )
    else:
        previous_traffic = models.Traffic.objects.get_earlier()
        if (
            conf.settings.require_init_data() and
            not previous_traffic.init_data
        ):
            init_traffic = models.Traffic.objects.get_init()

            if init_traffic.tx_bytes == 0 and init_traffic.rx_bytes == 0:
                conf.settings.set_require_init_data(False)
            elif (
                previous_traffic.tx_bytes > tx_bytes or
                previous_traffic.rx_bytes > rx_bytes
            ):
                init_traffic.rx_bytes = 0
                init_traffic.tx_bytes = 0
                init_traffic.save()
                conf.settings.set_require_init_data(False)
            else:
                rx_bytes -= init_traffic.rx_bytes
                tx_bytes -= init_traffic.tx_bytes

        instance, _ = models.Traffic.objects.get_or_create(
            date=timezone.localtime(timezone.now()).date()
        )
        instance.interface = interfaces
        if (
            previous_traffic.rx_bytes > rx_bytes or
            previous_traffic.tx_bytes > tx_bytes
        ):
            instance.rx_bytes = rx_bytes
            instance.tx_bytes = tx_bytes
        else:
            instance.rx_bytes = rx_bytes - previous_traffic.rx_bytes
            instance.tx_bytes = tx_bytes - previous_traffic.tx_bytes
        instance.updated_at = timezone.now()
        instance.save()

        check_traffic_limit(instance.total())
