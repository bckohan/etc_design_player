from django.views.generic import TemplateView
from django.conf import settings
from .models import PlaybackSettings, ManualOverride, Playlist
import subprocess


class ControlView(TemplateView):
    template_name = 'etc_player/control.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = PlaybackSettings.load()
        context['playlists'] = Playlist.objects.all()
        return context

    @staticmethod
    def restart_audio():
        subprocess.run(settings.RESTART_COMMAND.split())

    @staticmethod
    def set_volume(volume):
        subprocess.run(settings.VOLUME_COMMAND.format(
            volume=max(0, min(100, int(volume)))
        ).split())

    def get(self, request, *args, **kwargs):
        settings = PlaybackSettings.load()
        do_stop = request.GET.get('stop', None) is not None
        do_play = request.GET.get('play', None) is not None
        volume = request.GET.get('volume', None)
        playlist = request.GET.get('playlist', None)
        if playlist:
            playlist = Playlist.objects.get(pk=playlist)
        if volume is not None and settings.volume != volume:
            settings.volume = volume
            settings.save()
            self.set_volume(volume)
        if do_stop:
            ManualOverride.objects.create(
                operation=ManualOverride.Operation.STOP
            )
            self.restart_audio()
        elif do_play:
            ManualOverride.objects.create(
                operation=ManualOverride.Operation.PLAY,
                playlist=playlist
            )
            self.restart_audio()
        return super().get(request, *args, **kwargs)
