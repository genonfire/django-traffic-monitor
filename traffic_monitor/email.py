from smtplib import SMTPException

from django.core.mail import (
    BadHeaderError,
    EmailMultiAlternatives
)
from django.template.loader import render_to_string

from . import conf


class _EmailHelper(object):
    def _recipient_list(self, recipients):
        if isinstance(recipients, list):
            return recipients

        data = []
        for index, recipient in enumerate(recipients.split(',')):
            data.append(recipient.strip())
        return data

    def _send(
        self, subject, body, from_email=None, to=None, bcc=None, cc=None,
        html_subject=None, html_body=None, attachment=None, filename=None,
        mimetype=None, context=None
    ):
        if not conf.settings.TRAFFIC_MONITOR_ALARM_SEND_EMAIL:
            return

        if html_subject:
            subject = render_to_string(html_subject, context)
        subject = ''.join(subject.splitlines())

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to,
            bcc=bcc,
            cc=cc
        )
        if html_body:
            html_email = render_to_string(html_body, context)
            email.attach_alternative(html_email, 'text/html')
        if attachment and filename and mimetype:
            email.attach(filename, attachment, mimetype)

        try:
            email.send(fail_silently=False)
        except BadHeaderError:
            print("BadHeaderError")
        except SMTPException:
            print("SMTPException")

    def send(
        self, subject, body, from_email=None, to=None, html_subject=None,
        html_body=None, attachment=None, filename=None, mimetype=None,
        context=None
    ):
        self._send(
            subject=subject,
            body=body,
            from_email=conf.settings.TRAFFIC_MONITOR_EMAIL_FROM,
            to=conf.settings.TRAFFIC_MONITOR_EMAIL_TO,
            html_subject=html_subject,
            html_body=html_body,
            attachment=attachment,
            filename=filename,
            mimetype=mimetype,
            context=context
        )


EmailHelper = _EmailHelper()
