from django.apps import AppConfig
from django.db.models.signals import (
    pre_save,
    post_save,
    post_delete,
    pre_delete
)
from django.conf import settings
from django.db import transaction
import os


def cache_playing(sender, instance, **kwargs):
    from .models import PlaybackSettings
    instance._now_playing = PlaybackSettings.load().current_playlist


def check_restart(sender, instance, **kwargs):
    from .utils import restart_audio
    """Restart audio if the schedule has changed."""
    from .models import PlaybackSettings
    now_playing = getattr(instance, '_now_playing', None)
    if (
        now_playing is None or
        now_playing != PlaybackSettings.load().current_playlist
    ):
        # restart audio is throttled so we want to do it at the end
        transaction.on_commit(lambda: restart_audio())


def do_delete(path):
    if os.path.exists(path):
        os.remove(path)


def delete_file(sender, instance, **kwargs):
    if os.path.exists(instance.file.path):
        transaction.on_commit(lambda: do_delete(instance.file.path))


def synchronize_volume(sender, instance, **kwargs):
    from .utils import set_volume
    set_volume(instance.volume)


class ETCPlayerConfig(AppConfig):
    name = 'etc_player'

    @staticmethod
    def register_receivers():
        from etc_player.models import (
            PlaybackSettings,
            PlaybackTimeRange,
            ManualOverride,
            Wave,
            Playlist
        )

        for model in [PlaybackTimeRange, ManualOverride, Wave, Playlist]:
            pre_save.connect(
                cache_playing,
                sender=model
            )
            pre_delete.connect(
                cache_playing,
                sender=model
            )
            post_save.connect(
                check_restart,
                sender=model
            )
            post_delete.connect(
                check_restart,
                sender=model
            )

        post_save.connect(synchronize_volume, sender=PlaybackSettings)

        post_delete.connect(
            delete_file,
            sender=Wave
        )

    def ready(self):
        if not getattr(settings, 'TEST', False):
            self.register_receivers()
