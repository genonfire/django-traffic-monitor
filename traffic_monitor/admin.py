from django.contrib import admin

from . import models


@admin.register(models.Traffic)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'interface',
        'rx_bytes',
        'tx_bytes',
        'date',
        'updated_at',
        'init_data',
    )
    search_fields = (
        'id',
        'interface',
        'date',
    )
    ordering = (
        '-updated_at',
        '-id',
    )
    list_display_links = (
        'id',
        'interface',
    )
