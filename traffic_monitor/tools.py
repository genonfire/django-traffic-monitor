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
        print('SKIP: TRAFFIC_MONITOR_ALARM_SEND_EMAIL.')
        return SKIP

    last_total_bytes = conf.settings.get_last_total_bytes()
    if last_total_bytes == 0:
        return DO_NOT_SKIP

    bytes_threshold = conf.settings.TRAFFIC_MONITOR_ALARM_BYTES_THRESHOLD

    if total_bytes > last_total_bytes + bytes_threshold:
        return DO_NOT_SKIP

    print('SKIP: %s < %s + %s' % (
        print_unit(total_bytes),
        print_unit(last_total_bytes),
        print_unit(bytes_threshold)
    ))
    return SKIP


def send_email_alarm(today_total, month_total):
    subject = conf.settings.TRAFFIC_MONITOR_ALARM_EMAIL_SUBJECT
    today_unit = print_unit(today_total)
    month_unit = print_unit(month_total)

    print('code yellow today(%s), month(%s)' % (today_unit, month_unit))

    EmailHelper.send(
        subject=subject,
        body='traffic_monitor/alarm.html',
        html_body='traffic_monitor/alarm.html',
        context={
            'subject': subject,
            'alert_at': timezone.now(),
            'today_total': today_unit,
            'month_total': month_unit,
        }
    )

    conf.settings.set_last_total_bytes(today_total)


def check_traffic_limit(today_total):
    if skip_alarm(today_total):
        return

    daily_limit = conf.settings.TRAFFIC_MONITOR_DAILY_ALARM_BYTES
    monthly_limit = conf.settings.TRAFFIC_MONITOR_MONTHLY_ALARM_BYTES
    code_yellow = False

    print('today(%s), limit(%s/%s)' % (
        print_unit(today_total),
        print_unit(daily_limit),
        print_unit(monthly_limit)
    ))

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

    rx_read = tx_read = 0

    system = platform.system()
    if system == 'Linux':
        for interface in interfaces.split(','):
            path = '/sys/class/net/%s/statistics/' % interface
            try:
                with open(os.path.join(path, "rx_bytes")) as f:
                    rx_read += int(f.read())
                with open(os.path.join(path, "tx_bytes")) as f:
                    tx_read += int(f.read())
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
                    rx_read += int(f.read())
                with open(os.path.join(path, "tx_bytes")) as f:
                    tx_read += int(f.read())
            except IOError:
                print('Failed to open file from %s' % path)
    else:
        raise NotImplementedError("%s is not supported." % system)

    if not models.Traffic.objects.exists():
        models.Traffic.objects.create_init(
            interface=interfaces,
            rx_read=rx_read,
            tx_read=tx_read
        )
    else:
        previous_traffic = models.Traffic.objects.get_earlier()

        instance, created = models.Traffic.objects.get_or_create(
            date=timezone.localtime(timezone.now()).date()
        )
        instance.interface = interfaces
        instance.rx_read = rx_read
        instance.tx_read = tx_read

        if created:
            conf.settings.set_last_total_bytes(0)

        if (
            previous_traffic.rx_read > rx_read or
            previous_traffic.tx_read > tx_read
        ):
            instance.rx_bytes = rx_read
            instance.tx_bytes = tx_read
        else:
            instance.rx_bytes = rx_read - previous_traffic.rx_read
            instance.tx_bytes = tx_read - previous_traffic.tx_read

        instance.updated_at = timezone.now()
        instance.save()

        check_traffic_limit(instance.total())
