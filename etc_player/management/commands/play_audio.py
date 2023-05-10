from django.core.management.base import BaseCommand, CommandError
from etc_player.models import PlaybackSettings


class Command(BaseCommand):
    help = "Play the audio given the playback settings."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        settings = PlaybackSettings.load()
