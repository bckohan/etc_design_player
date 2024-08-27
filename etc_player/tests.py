from django.test import TransactionTestCase
from .models import ManualOverride, PlaybackSettings, PlaybackTimeRange, Playlist, Wave
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.test import Client
from django.db import transaction
from unittest import skipIf
from datetime import timedelta, datetime, time
from time import sleep
import io
import math
import wave
import struct
import os


class BeepGenerator:
    def __init__(self):
        # Audio will contain a long list of samples (i.e. floating point
        # numbers describing the waveform).  If you were working with a very
        # long sound you'd want to stream this to disk instead of buffering it
        # all in memory list this.  But most sounds will fit in memory.
        self.audio = []
        self.sample_rate = 44100.0
        self.buffer = io.BytesIO()

    def append_silence(self, duration_milliseconds=500):
        """
        Adding silence is easy - we add zeros to the end of our array
        """
        num_samples = duration_milliseconds * (self.sample_rate / 1000.0)

        for x in range(int(num_samples)):
            self.audio.append(0.0)

        return

    def append_sinewave(self, freq=440.0, duration_milliseconds=500, volume=1.0):
        """
        The sine wave generated here is the standard beep.  If you want
        something more aggressive you could try a square or saw tooth waveform.
        Though there are some rather complicated issues with making high
        quality square and sawtooth waves... which we won't address here :)
        """

        num_samples = duration_milliseconds * (self.sample_rate / 1000.0)

        for x in range(int(num_samples)):
            self.audio.append(
                volume * math.sin(2 * math.pi * freq * (x / self.sample_rate))
            )

        return

    def get_bytes(self):
        # Open up a wav file
        wav_file = wave.open(self.buffer, "w")

        # wav params
        nchannels = 1

        sampwidth = 2

        # 44100 is the industry standard sample rate - CD quality.  If you need
        # to save on file size you can adjust it downwards. The stanard for low
        # quality is 8000 or 8kHz.
        nframes = len(self.audio)
        comptype = "NONE"
        compname = "not compressed"
        wav_file.setparams(
            (nchannels, sampwidth, self.sample_rate, nframes, comptype, compname)
        )

        # WAV files here are using short, 16 bit, signed integers for the
        # sample size.  So we multiply the floating point data we have by
        # 32767, the maximum value for a short integer.  NOTE: It is
        # theortically possible to use the floating point -1.0 to 1.0 data
        # directly in a WAV file but not obvious how to do that using the wave
        # module in python.
        for sample in self.audio:
            wav_file.writeframes(struct.pack("h", int(sample * 32767.0)))

        wav_file.close()

        self.buffer.seek(0)
        return self.buffer.read()


if __name__ == "__main__":
    bg = BeepGenerator()


class PlayerTests(TransactionTestCase):
    """
    some of these scheduling tests might break if run straddling the seconds
    around midnight b/c of the day boundary - safe to ignore
    """

    wave1 = None
    wave2 = None

    wave_path1 = None
    wave_path2 = None

    playlist1 = None
    playlist2 = None

    settings: PlaybackSettings

    user = None

    restarted = False
    volume_set = False
    volume_value = None

    def setUp(self):
        from etc_player import utils
        from etc_player.apps import ETCPlayerConfig

        def restarted():
            self.restarted = True

        def volume_set(volume):
            self.volume_set = True
            self.volume_value = volume

        utils.restart_audio = restarted
        utils.set_volume = volume_set

        ETCPlayerConfig.register_receivers()

        self.user = get_user_model().objects.create_superuser(
            username="test", email="noreply@localhost", password="test"
        )

        bg1 = BeepGenerator()
        bg1.append_sinewave(volume=0.25, duration_milliseconds=100)
        bg1.append_silence()
        bg1.append_sinewave(volume=0.5, duration_milliseconds=700)
        bg1.append_silence()

        bg2 = BeepGenerator()
        bg2.append_sinewave(volume=0.45, duration_milliseconds=1300)
        bg2.append_silence()
        bg2.append_sinewave(volume=0.6, duration_milliseconds=800)
        bg2.append_silence()

        wave_file1 = ContentFile(bg1.get_bytes(), name="wave_file1.wav")
        wave_file2 = ContentFile(bg2.get_bytes(), name="wave_file2.wav")

        self.wave1 = Wave.objects.create(file=wave_file1)
        self.wave2 = Wave.objects.create(file=wave_file2)

        self.wave_path1 = self.wave1.file.path
        self.wave_path2 = self.wave2.file.path

        self.playlist1 = Playlist.objects.create(name="Playlist 1")
        self.playlist1.waves.add(self.wave1)
        self.playlist1.waves.add(self.wave2)
        self.playlist2 = Playlist.objects.create(name="Playlist 2")
        self.playlist2.waves.add(self.wave2)

        self.settings = PlaybackSettings.load()
        self.settings.default_playlist = self.playlist2
        self.settings.save()

        Client().login(username="test", password="test")

        self.restarted = False
        self.volume_set = False

    def tearDown(self) -> None:
        for wave_file in [self.wave_path1, self.wave_path2]:
            if os.path.exists(wave_file):
                os.remove(wave_file)
        ManualOverride.objects.all().delete()
        Playlist.objects.all().delete()
        PlaybackTimeRange.objects.all().delete()
        Wave.objects.all().delete()

    def test_duration(self):
        self.assertEqual(self.playlist1.duration_str, "4 seconds")
        self.assertEqual(self.playlist2.duration_str, "3 seconds")

    def check_time_range_consistency(self):
        self.assertRaises(
            Exception,
            PlaybackTimeRange.objects.create(
                day_of_week=0, start_time=time(hour=5), end_time=time(hour=4)
            ),
        )

        self.assertRaises(
            Exception,
            PlaybackTimeRange.objects.create(
                day_of_week=0, start_time=time(hour=5), end_time=time(hour=5)
            ),
        )

    def test_next_and_last_scheduled(self):
        current_time = datetime.now() + timedelta(seconds=10)
        dow = PlaybackTimeRange.DayOfWeek(current_time)
        days = [current_time + timedelta(days=days) for days in range(0, 7)]

        for idx, dt in enumerate(days):
            playlist = self.playlist1 if idx % 2 == 0 else self.playlist2
            pb_range = PlaybackTimeRange.objects.create(
                day_of_week=dt,
                playlist=playlist,
                start=dt.time(),
                end=(dt + timedelta(seconds=1)).time(),
            )
            next_dt, next_sched = PlaybackTimeRange.objects.next_scheduled_playlist()
            last_dt, last_sched = PlaybackTimeRange.objects.last_scheduled_playlist()
            self.assertEqual(next_dt, dt)
            self.assertEqual(next_sched.playlist, playlist)
            self.assertEqual(last_dt, dt - timedelta(days=7))
            self.assertEqual(last_sched.playlist, playlist)
            pb_range.delete()

        for idx, dt in enumerate(days):
            playlist = self.playlist1 if idx % 2 == 0 else self.playlist2
            PlaybackTimeRange.objects.create(
                day_of_week=dt,
                playlist=playlist,
                start=dt.time(),
                end=(dt + timedelta(seconds=1)).time(),
            )
            next_dt, next_sched = PlaybackTimeRange.objects.next_scheduled_playlist()
            last_dt, last_sched = PlaybackTimeRange.objects.last_scheduled_playlist()
            self.assertEqual(next_dt, current_time)
            self.assertEqual(next_sched.playlist, self.playlist1)
            self.assertEqual(last_dt, current_time - timedelta(days=7 - idx))
            self.assertEqual(last_sched.playlist, playlist)

        PlaybackTimeRange.objects.all().delete()

    def test_basic_manual_use(self):
        # Pressing play with no schedule should play the default playlist
        self.assertIsNone(self.settings.current_playlist)
        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        override = ManualOverride.objects.create(
            operation=ManualOverride.Operation.PLAY
        )
        self.assertEqual(self.settings.current_playlist, self.playlist2)
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.restarted = False
        self.volume_set = False

        # deleting the play should stop the playlist
        override.delete()
        self.assertEqual(self.settings.current_playlist, None)
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.restarted = False
        self.volume_set = False

        # playlist field on override is honored
        override = ManualOverride.objects.create(
            operation=ManualOverride.Operation.PLAY, playlist=self.playlist1
        )
        self.assertEqual(self.settings.current_playlist, self.playlist1)
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.restarted = False
        self.volume_set = False

        # hitting the stop button works
        ManualOverride.objects.create(operation=ManualOverride.Operation.STOP)
        self.assertEqual(self.settings.current_playlist, None)
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.restarted = False
        self.volume_set = False

        ManualOverride.objects.all().delete()
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)

    def test_basic_schedule_use(self):
        # schedule into the near future - watch as playback should start
        current_time = datetime.now()

        start = current_time + timedelta(seconds=5)
        end = current_time + timedelta(seconds=8)

        time_range = PlaybackTimeRange.objects.create(
            day_of_week=PlaybackTimeRange.DayOfWeek(start),
            start=start.time(),
            end=end.time(),
            playlist=self.playlist1,
        )

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertIsNone(self.settings.current_playlist)

        self.restarted = False
        self.volume_set = False

        sleep(5)

        self.assertEqual(self.settings.current_playlist, self.playlist1)

        sleep(4)

        # active playlist is empty
        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertIsNone(self.settings.current_playlist)

        # time range extension past current time should trigger restart
        time_range.end = (datetime.now() + timedelta(seconds=5)).time()
        time_range.save()

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist1)

        self.restarted = False
        self.volume_set = False

        # active playlist change should trigger audio restart
        time_range.playlist = self.playlist2
        time_range.save()
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist2)

        self.restarted = False
        self.volume_set = False

        # delete active schedule - should trigger audio restart and no playlist
        time_range.delete()
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertIsNone(self.settings.current_playlist)

        self.restarted = False
        self.volume_set = False

    def test_manual_override(self):
        current_time = datetime.now()

        start = current_time
        end = current_time + timedelta(seconds=5)

        time_range = PlaybackTimeRange.objects.create(
            day_of_week=start, start=start.time(), end=end.time()
        )

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)

        # playlist should be default
        self.assertEqual(self.settings.current_playlist, self.playlist2)

        self.restarted = False
        self.volume_set = False

        play = ManualOverride.objects.create(
            operation=ManualOverride.Operation.PLAY, playlist=self.playlist1
        )
        self.assertEqual(self.settings.current_playlist, self.playlist1)
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)

        self.restarted = False
        self.volume_set = False

        play.delete()

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist2)

        self.restarted = False
        self.volume_set = False

        stop = ManualOverride.objects.create(
            operation=ManualOverride.Operation.STOP, playlist=self.playlist1
        )

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertIsNone(self.settings.current_playlist)

        self.restarted = False
        self.volume_set = False

        stop.delete()

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist2)

        self.restarted = False
        self.volume_set = False

        # should still play after time expires because of manual override
        play = ManualOverride.objects.create(operation=ManualOverride.Operation.PLAY)
        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist2)

        sleep(5)

        self.restarted = False
        self.volume_set = False

        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)

        self.assertEqual(self.settings.current_playlist, self.playlist2)

        time_range.delete()

        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist2)

        start = datetime.now() + timedelta(seconds=2)
        end = start + timedelta(seconds=3)
        time_range = PlaybackTimeRange.objects.create(
            day_of_week=PlaybackTimeRange.DayOfWeek(start),
            start=start.time(),
            end=end.time(),
            playlist=self.playlist1,
        )

        self.assertEqual(self.settings.current_playlist, self.playlist2)
        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)

        sleep(3)

        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist1)

        sleep(4)

        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertIsNone(self.settings.current_playlist)

        self.playlist1.delete()

        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.assertEqual(self.settings.current_playlist, self.playlist2)

    def test_override_in_future_bug(self):
        ManualOverride.objects.all().delete()
        PlaybackTimeRange.objects.all().delete()
        self.assertEqual(self.settings.current_playlist, None)

        start = datetime.now() + timedelta(seconds=2)
        end = datetime.now() + timedelta(seconds=5)

        ManualOverride.objects.create(
            operation=ManualOverride.Operation.PLAY,
            timestamp=start,
            playlist=self.playlist1,
        )
        ManualOverride.objects.create(
            operation=ManualOverride.Operation.STOP,
            timestamp=end,
            playlist=self.playlist1,
        )

        self.assertEqual(ManualOverride.objects.count(), 2)
        self.assertEqual(self.settings.current_playlist, None)
        sleep(3)
        self.assertTrue(start < datetime.now() < end)
        playing = self.settings.current_playlist
        self.assertEqual(ManualOverride.objects.count(), 2)
        self.assertEqual(playing, self.playlist1)
        sleep((end - datetime.now()).total_seconds() + 1)
        self.assertEqual(self.settings.current_playlist, None)
        self.assertEqual(ManualOverride.objects.count(), 2)

    def test_set_volume(self):
        self.volume_set = False
        self.volume_value = None

        self.settings.volume = 75
        self.settings.save()

        self.assertTrue(self.volume_set)
        self.assertEqual(self.volume_value, 75)

        self.volume_set = False

        self.settings.volume = 75
        self.settings.save()

        # self.assertTrue(self.volume_set)
        self.assertEqual(self.volume_value, 75)

        self.settings.volume = 50
        self.settings.save()

        self.assertTrue(self.volume_set)
        self.assertEqual(self.volume_value, 50)

    @skipIf(os.getenv("GITHUB_ACTIONS") == "true", "Skipped on GitHub Actions")
    def test_play_audio(self):
        self.assertIsNone(self.settings.current_playlist)
        self.assertFalse(self.restarted)
        self.assertFalse(self.volume_set)
        PlaybackTimeRange.objects.create(
            day_of_week=datetime.now(),
            start=datetime.now().time(),
            end=(datetime.now() + timedelta(seconds=2)).time(),
        )
        self.assertEqual(self.settings.current_playlist, self.playlist2)
        self.assertTrue(self.restarted)
        self.assertFalse(self.volume_set)
        self.restarted = False
        self.volume_set = False

        call_command("play_audio", terminate=True)

        response = input("Did you hear beeps (y/n)?")
        self.assertTrue(response.lower() in ["y", "yes", "1", "true"])

    def test_stop_last_week_same_day_bug(self):
        """
        Test found bug where if there is a manual STOP at the top of the stack
        for the same day of the week as the current day, but in the past it
        will block scheduled play.
        """

        today = datetime.now()
        last_week = today - timedelta(days=7)

        ManualOverride.objects.create(
            operation=ManualOverride.Operation.STOP,
            playlist=self.playlist1,
            timestamp=last_week,
        )

        PlaybackTimeRange.objects.create(
            day_of_week=today,
            start=today.time(),
            end=(today + timedelta(seconds=5)).time(),
            playlist=self.playlist1,
        )

        self.assertEqual(self.settings.current_playlist, self.playlist1)


class TestFileDeletion(TransactionTestCase):
    wave_file = None
    wave_file_path = None

    def setUp(self) -> None:
        bg3 = BeepGenerator()
        bg3.append_sinewave(volume=0.7, duration_milliseconds=500)
        bg3.append_silence()
        bg3.append_sinewave(volume=0.2, duration_milliseconds=120)
        bg3.append_silence()

        self.wave_file = Wave.objects.create(
            file=ContentFile(bg3.get_bytes(), name="wave_file3.wav")
        )
        self.wave_file_path = self.wave_file.file.path

    def tearDown(self) -> None:
        if self.wave_file_path:
            if os.path.exists(self.wave_file_path):
                os.remove(self.wave_file_path)

    def test_file_deletion(self):
        """
        Test that waves files are removed from disk when deleted from the
        database.
        """
        self.assertTrue(os.path.exists(self.wave_file_path))

        with transaction.atomic():
            self.wave_file.delete()

        self.assertFalse(os.path.exists(self.wave_file_path))
