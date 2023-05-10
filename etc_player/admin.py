"""
Admin interface for all models in etc_player.
"""
from django.contrib import admin
from .models import (
    PlaybackSettings,
    Playlist,
    PlaylistWave,
    Wave,
    PlaybackTimeRange
)


class PlaybackTimeRangeAdmin(admin.ModelAdmin):
    pass


class PlaybackSettingsAdmin(admin.ModelAdmin):
    pass


class PlaylistWaveAdmin(admin.TabularInline):
    model = PlaylistWave
    verbose_name_plural = 'Waves'
    extra = 0


class PlaylistAdmin(admin.ModelAdmin):
    inlines = [PlaylistWaveAdmin]


class WaveAdmin(admin.ModelAdmin):
    pass


admin.site.register(PlaybackTimeRange, PlaybackTimeRangeAdmin)
admin.site.register(PlaybackSettings, PlaybackSettingsAdmin)
admin.site.register(Playlist, PlaylistAdmin)
admin.site.register(Wave, WaveAdmin)
