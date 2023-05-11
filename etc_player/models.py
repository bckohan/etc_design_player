from django.db import models
from django.db.models import Q
from django_enum import EnumField
from enum_properties import IntEnumProperties, s
from django.core.cache import cache
from datetime import date, datetime
from django.utils.timezone import localtime, make_aware
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
import wave
import contextlib
import os


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache()

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)

    def set_cache(self):
        cache.set(self.__class__.__name__, self)


class Playlist(models.Model):

    name = models.CharField(blank=True, default='', max_length=255)
    waves = models.ManyToManyField(
        'etc_player.Wave',
        through='etc_player.PlaylistWave'
    )

    def __str__(self):
        return self.name


class PlaylistWave(models.Model):

    wave = models.ForeignKey(
        'etc_player.Wave',
        null=False,
        on_delete=models.CASCADE
    )
    playlist = models.ForeignKey(
        'etc_player.Playlist',
        null=False,
        on_delete=models.CASCADE
    )

    order = models.PositiveSmallIntegerField(
        null=False,
        blank=False
    )

    class Meta:
        ordering = ['order']


class Wave(models.Model):

    file = models.FileField(upload_to='uploads/')
    name = models.CharField(blank=True, default='', max_length=255)
    length = models.DurationField(null=True, default=None, blank=True)

    def save(self, *args, **kwargs):
        if (
            self.length is None and
            self.file.path is not None and
            os.path.exists(self.file.path)
        ):
            with contextlib.closing(wave.open(self.file.path, 'r')) as wave_file:
                frames = wave_file.getnframes()
                rate = wave_file.getframerate()
                self.length = timedelta(seconds=frames / float(rate))

        if not self.name:
            self.name = os.path.basename(self.file.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PlaybackTimeRangeManager(models.Manager):

    def scheduled_playlist(self):
        current_time = localtime()
        return self.get_queryset().filter(
            Q(day_of_week=PlaybackTimeRange.DayOfWeek(current_time)) &
            Q(start__lte=current_time.time()) &
            Q(end__gte=current_time.time())
        ).first()

    def next_scheduled_time(self):
        current_time = localtime()
        current_dow = PlaybackTimeRange.DayOfWeek(current_time).value
        dow = current_dow + 1 if current_dow < 6 else 0
        next_sched = self.get_queryset().filter(
            Q(day_of_week__gte=dow) |
            (Q(day_of_week=current_dow) & Q(start__gte=current_time.time()))
        ).first()
        if next_sched is None:
            next_sched = self.get_queryset().filter(day_of_week__gte=0).first()
        if next_sched is not None:
            dow = next_sched.day_of_week.value
            next_dt = make_aware(
                datetime.combine(
                    (current_time.date() + timedelta(
                        days=(
                            dow + 7 - current_dow
                            if dow < current_dow else dow - current_dow
                        )
                    )),
                    next_sched.start
                )
            )
            if next_dt < current_time:
                next_dt += timedelta(days=7)
            return next_dt, next_sched.playlist
        return None, None


class PlaybackTimeRange(models.Model):

    objects = PlaybackTimeRangeManager()

    class DayOfWeek(IntEnumProperties, s('label', case_fold=True)):

        SUNDAY    = 0, 'Sunday'
        MONDAY    = 1, 'Monday'
        TUESDAY   = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY  = 4, 'Thursday'
        FRIDAY    = 5, 'Friday'
        SATURDAY  = 6, 'Saturday'

        @classmethod
        def _missing_(cls, value):
            if isinstance(value, (date, datetime)):
                return cls(value.isoweekday())
            return super()._missing_(value)

    day_of_week = EnumField(DayOfWeek, unique=True)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    start = models.TimeField(db_index=True)
    end = models.TimeField(db_index=True)

    def __str__(self):
        return f'{self.day_of_week.label} {self.start} - {self.end}'

    class Meta:
        ordering = ['day_of_week', 'start']
        verbose_name_plural = 'Schedule'
        verbose_name = 'Schedule'


class ManualOverride(models.Model):

    class Operation(IntEnumProperties, s('label', case_fold=True)):

        PLAY = 0, 'Play'
        STOP = 1, 'Stop'

    operation = EnumField(Operation)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if self.playlist is None:
            if self.operation is ManualOverride.Operation.PLAY:
                self.playlist = PlaybackSettings.load().default_playlist
            else:
                self.playlist = PlaybackTimeRange.objects.scheduled_playlist().playlist
        super().save(*args, **kwargs)

    @property
    def effective_playlist(self):
        return self.playlist or PlaybackSettings.load().default_playlist

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Manual Overrides'
        verbose_name = 'Manual Override'


class PlaybackSettings(SingletonModel):

    volume = models.PositiveSmallIntegerField(
        null=False,
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    default_playlist = models.ForeignKey(
        'etc_player.Playlist',
        null=True,
        default=None,
        blank=True,
        on_delete=models.SET_NULL
    )

    @property
    def current_playlist(self):
        """
        Get the playlist that should be currently playing. We use the following
        state machine:

        - If there is no manual override, use the scheduled playlist if any
        - If there is no scheduled playlist and there have been no scheduled
            playlists since the last manual override use the manual override
        - If there is a currently scheduled playlist use that unless the most
            recent manual override has happened since the playlist's scheduled
            start time, in which case use the manual override

        :return: None if nothing should be playing, otherwise the playlist
        """
        current_time = localtime()
        override = ManualOverride.objects.first()
        scheduled = PlaybackTimeRange.objects.scheduled_playlist()
        if override is None:
            return getattr(scheduled, 'playlist', None)
        elif scheduled is None:
            if override.operation is override.Operation.PLAY:
                override_dow = PlaybackTimeRange.DayOfWeek(override.timestamp)
                override_time = override.timestamp.time()

                tot_days_between = (current_time - override.timestamp).days
                if tot_days_between < 7:
                    days_between = set([
                        PlaybackTimeRange.DayOfWeek(
                            override.timestamp + timedelta(days=day)
                        )
                        for day in range(0, tot_days_between) if day > 0
                    ])
                    scheduled_since = PlaybackTimeRange.objects.filter(
                        (Q(day_of_week=override_dow) & Q(
                            start__gte=override_time))
                        | Q(day_of_week__in=days_between)
                    ).first()
                else:
                    scheduled_since = True

                if not scheduled_since:
                    return override.playlist
            return None
        else:
            override_dow = PlaybackTimeRange.DayOfWeek(override.timestamp)
            if (
                override_dow is not scheduled.day_of_week or
                override.timestamp.time() < scheduled.start
            ):
                return scheduled.playlist
            elif override.operation is override.Operation.PLAY:
                return override.playlist
        return None

    class Meta:
        verbose_name_plural = 'Playback Settings'
        verbose_name = 'Playback Settings'
