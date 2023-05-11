"""
Admin interface for all models in etc_player.
"""
from django.contrib import admin
from .models import (
    PlaybackSettings,
    Playlist,
    PlaylistWave,
    Wave,
    PlaybackTimeRange,
    ManualOverride
)
from django import forms


class TimeInput(forms.widgets.TimeInput):
    input_type = 'time'


class PlaybackTimeRangeForm(forms.ModelForm):

    class Meta:
        model = PlaybackTimeRange
        widgets = {
            'start': TimeInput(),
            'end': TimeInput()
        }
        fields = '__all__'


class PlaybackTimeRangeAdmin(admin.ModelAdmin):
    form = PlaybackTimeRangeForm


class PlaybackSettingsAdmin(admin.ModelAdmin):
    pass


class PlaylistWaveAdmin(admin.TabularInline):
    model = PlaylistWave
    verbose_name_plural = 'Waves'
    extra = 0


class PlaylistAdmin(admin.ModelAdmin):
    inlines = [PlaylistWaveAdmin]


class WaveAdmin(admin.ModelAdmin):
    readonly_fields = ['length']


class ManualOverrideAdmin(admin.ModelAdmin):
    pass


admin.site.register(PlaybackTimeRange, PlaybackTimeRangeAdmin)
admin.site.register(PlaybackSettings, PlaybackSettingsAdmin)
admin.site.register(Playlist, PlaylistAdmin)
admin.site.register(Wave, WaveAdmin)
admin.site.register(ManualOverride, ManualOverrideAdmin)
