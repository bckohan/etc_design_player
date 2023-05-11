from django.core.management.base import BaseCommand
from etc_player.models import PlaybackSettings, PlaybackTimeRange
from django.utils.timezone import localtime
from django.conf import settings
import subprocess
import wave
import time


class Command(BaseCommand):
    help = "Play the audio given the playback settings."

    CHUNK = 8192

    settings = None

    def add_arguments(self, parser):

        parser.add_argument(
            '--chunk-size',
            dest='chunk_size',
            default=self.CHUNK,
            type=int,
            help=f'The number of bytes to buffer at a time from the wave file.'
                 '(This only applies when using pyaudio).'
                 'Default: {self.CHUNK}'
        )

    def handle(self, *args, **options):
        self.CHUNK = options.get('chunk_size', self.CHUNK)
        self.run()

    def run(self):
        self.settings = PlaybackSettings.load()
        playlist = self.settings.current_playlist
        while playlist:
            self.stdout.write(
                self.style.SUCCESS(f'Playing: {playlist.name}')
            )
            self.play_playlist(playlist)
            playlist = self.settings.current_playlist

        nxt_time, nxt_list = PlaybackTimeRange.objects.next_scheduled_time()
        if nxt_time is None:
            self.style.WARNING('No scheduled playbacks.')
            return
        wait_seconds = (nxt_time - localtime()).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(
                f'Playing {nxt_list.name} in {wait_seconds} seconds @ '
                f'{nxt_time}.'
            )
        )
        time.sleep(wait_seconds)
        self.run()

    def play_playlist(self, playlist):
        for wave_file in playlist.waves.all():
            self.play_wave(wave_file)
            current_playlist = self.settings.current_playlist
            if playlist != current_playlist:
                if current_playlist:
                    return self.play_playlist(current_playlist)
                else:
                    return

    def play_wave_pyaudio(self, wave_file):
        import pyaudio

        with wave.open(wave_file.file.path, 'rb') as wf:
            # Instantiate PyAudio and initialize PortAudio system resources (1)
            p = pyaudio.PyAudio()

            # Open stream (2)
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                frames_per_buffer=self.CHUNK
            )

            # Play samples from the wave file (3)
            data = wf.readframes(self.CHUNK)
            while len(data) > 0:
                stream.write(data)
                data = wf.readframes(self.CHUNK)

            # Close stream (4)
            stream.close()

            # Release PortAudio system resources (5)
            p.terminate()

    def play_wave(self, wave_file):
        play_cmd = getattr(settings, 'PLAY_COMMAND', None)
        if play_cmd:
            subprocess.run(
                play_cmd.format(wave_file=wave_file.file.path).split()
            )
        else:
            self.play_wave_pyaudio(wave_file)
