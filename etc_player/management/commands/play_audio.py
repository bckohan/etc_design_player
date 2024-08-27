import subprocess
import time
import typing as t
import wave
from datetime import datetime

from django.conf import settings
from django.db.models import Q
from django_typer.management import TyperCommand
from typer import Option

from etc_player.models import ManualOverride, PlaybackSettings, PlaybackTimeRange


class Command(TyperCommand):
    help = "Play the audio given the playback settings."

    CHUNK = 8192
    USE_PYAUDIO = False
    MAX_SLEEP = None
    TERMINATE = False

    settings = None

    def handle(
        self,
        pyaudio: t.Annotated[
            bool,
            Option(
                "--pyaudio",
                help="Use pyaudio to play the audio instead of the configured play command.",
            ),
        ] = False,
        chunk_size: t.Annotated[
            int,
            Option(
                help="The number of bytes to buffer at a time from the wave file. "
                "(This only applies when using pyaudio)."
            ),
        ] = CHUNK,
        max_sleep: t.Annotated[
            t.Optional[int],
            Option(
                help="Limit sleeps to this many seconds. Default: no limit. This "
                "may be useful if clock drift is an issue."
            ),
        ] = MAX_SLEEP,
        terminate: t.Annotated[
            bool,
            Option(
                "--terminate",
                help="Terminate if nothing scheduled to play immediately.",
            ),
        ] = False,
    ):
        self.CHUNK = chunk_size
        self.USE_PYAUDIO = pyaudio
        self.MAX_SLEEP = max_sleep
        self.TERMINATE = terminate
        self.run()

    def run(self):
        self.settings = PlaybackSettings.load()
        playlist = self.settings.current_playlist
        while playlist:
            self.stdout.write(self.style.SUCCESS(f"Playing: {playlist.name}"))
            self.play_playlist(playlist)
            playlist = self.settings.current_playlist

        nxt_time, next_sched = PlaybackTimeRange.objects.next_scheduled_playlist()
        override = (
            ManualOverride.objects.filter(
                Q(timestamp__gte=datetime.now()) & Q(timestamp__lt=nxt_time)
            )
            .order_by("timestamp")
            .first()
        )
        if override:
            nxt_time = override.timestamp
        if nxt_time is None or self.TERMINATE:
            self.style.WARNING("No scheduled playbacks.")
            return
        wait_seconds = (nxt_time - datetime.now()).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(
                f"Playing {next_sched.playlist.name} in {wait_seconds} seconds @ "
                f"{nxt_time}."
            )
        )
        time.sleep(
            wait_seconds + 1
            if self.MAX_SLEEP is None
            else min(wait_seconds + 1, self.MAX_SLEEP)
        )
        self.run()

    def play_playlist(self, playlist):
        for wave_file in playlist.waves.all():
            if self.USE_PYAUDIO:
                self.play_wave_pyaudio(wave_file)
            else:
                self.play_wave(wave_file)
            current_playlist = self.settings.current_playlist
            if playlist != current_playlist:
                if current_playlist:
                    return self.play_playlist(current_playlist)
                else:
                    return

    def play_wave_pyaudio(self, wave_file):
        import pyaudio

        with wave.open(wave_file.file.path, "rb") as wf:
            # Instantiate PyAudio and initialize PortAudio system resources (1)
            p = pyaudio.PyAudio()

            # Open stream (2)
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                frames_per_buffer=self.CHUNK,
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
        play_cmd = getattr(settings, "PLAY_COMMAND", None)
        if play_cmd:
            try:
                subprocess.run(play_cmd.format(wave_file=wave_file.file.path).split())
            except Exception:
                self.play_wave_pyaudio(wave_file)
        else:
            self.play_wave_pyaudio(wave_file)
