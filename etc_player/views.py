from django.views.generic import TemplateView
from .models import PlaybackSettings, ManualOverride, Playlist


class ControlView(TemplateView):
    template_name = 'etc_player/control.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = PlaybackSettings.load()
        context['playlists'] = Playlist.objects.all()
        return context

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
        if do_stop:
            ManualOverride.objects.create(
                operation=ManualOverride.Operation.STOP
            )
        elif do_play:
            ManualOverride.objects.create(
                operation=ManualOverride.Operation.PLAY,
                playlist=playlist
            )
        return super().get(request, *args, **kwargs)
