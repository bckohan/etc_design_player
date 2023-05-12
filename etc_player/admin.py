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

    list_display = ('weekday', 'start_str', 'end_str', 'playlist')

    def weekday(self, obj):
        return obj.day_of_week.label

    weekday.short_description = 'Weekday'

    def start_str(self, obj):
        return obj.start.strftime("%I:%M %p")

    def end_str(self, obj):
        return obj.end.strftime("%I:%M %p")

    start_str.short_description = 'Start'
    end_str.short_description = 'End'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('playlist')


class PlaybackSettingsAdmin(admin.ModelAdmin):
    pass


class PlaylistWaveAdmin(admin.TabularInline):
    model = PlaylistWave
    verbose_name_plural = 'Waves'
    extra = 0


class PlaylistAdmin(admin.ModelAdmin):
    inlines = [PlaylistWaveAdmin]

    readonly_fields = ['duration_str']
    list_display = ('name', 'duration_str')

    def duration_str(self, obj):
        return obj.duration_str

    duration_str.short_description = 'Duration'


class WaveAdmin(admin.ModelAdmin):

    readonly_fields = ['duration_str', 'size']

    list_display = ('name', 'duration_str', 'size')

    def size(self, obj):
        return obj.size_str

    def duration_str(self, obj):
        return obj.duration_str

    duration_str.short_description = 'Duration'
    size.short_description = 'File Size'


class ManualOverrideAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('playlist')


admin.site.register(PlaybackTimeRange, PlaybackTimeRangeAdmin)
admin.site.register(PlaybackSettings, PlaybackSettingsAdmin)
admin.site.register(Playlist, PlaylistAdmin)
admin.site.register(Wave, WaveAdmin)
admin.site.register(ManualOverride, ManualOverrideAdmin)
