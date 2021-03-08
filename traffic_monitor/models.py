from django.db import models
from django.utils import timezone


class TrafficManager(models.Manager):
    def today(self):
        now = timezone.localtime(timezone.now())
        traffics = self.filter(date=now.date()).filter(init_data=False)
        if traffics.exists():
            return traffics.first()

    def this_month(self):
        now = timezone.localtime(timezone.now())
        return self.filter(date__year=now.year).filter(
            date__month=now.month).filter(init_data=False)

    def this_year(self):
        now = timezone.localtime(timezone.now())
        return self.filter(date__year=now.year).filter(init_data=False)

    def create_init(
        self, interface, rx_bytes=0, tx_bytes=0, rx_read=0, tx_read=0
    ):
        yesterday = (timezone.now() - timezone.timedelta(days=1)).date()
        instance = self.create(
            interface=interface,
            rx_bytes=rx_bytes,
            tx_bytes=tx_bytes,
            rx_read=rx_read,
            tx_read=tx_read,
            date=yesterday,
            init_data=True
        )
        return instance

    def get_init(self):
        return self.filter(init_data=True).first()

    def get_earlier(self):
        now = timezone.localtime(timezone.now())
        traffics = self.filter(date__lt=now.date())
        if traffics.exists():
            return traffics.latest('date')


class Traffic(models.Model):
    interface = models.CharField(max_length=254)
    rx_bytes = models.BigIntegerField(default=0)
    tx_bytes = models.BigIntegerField(default=0)
    rx_read = models.BigIntegerField(default=0)
    tx_read = models.BigIntegerField(default=0)
    date = models.DateField(unique=True)
    updated_at = models.DateTimeField(default=timezone.now)
    init_data = models.BooleanField(default=False)

    objects = TrafficManager()

    class Meta:
        ordering = ('-date', '-id')

    def total(self):
        return self.rx_bytes + self.tx_bytes
