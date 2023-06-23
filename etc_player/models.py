from django.db import models
from django.db.models import Q, Sum, F, CheckConstraint
from django_enum import EnumField
from enum_properties import IntEnumProperties, s
from django.core.cache import cache
from datetime import timedelta, datetime, date
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.functional import cached_property
from .utils import sizeof_fmt, duration_fmt
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

    @cached_property
    def duration(self):
        return self.waves.all().aggregate(Sum('duration'))['duration__sum']

    @property
    def duration_str(self):
        return duration_fmt(self.duration)

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
        blank=False,
        default=0
    )

    @property
    def duration_str(self):
        return self.wave.duration_str

    class Meta:
        ordering = ['order']


class Wave(models.Model):

    file = models.FileField(upload_to='uploads/')
    name = models.CharField(blank=True, default='', max_length=255)
    duration = models.DurationField(
        null=True,
        default=None,
        blank=True,
        editable=False
    )

    @property
    def duration_str(self):
        return duration_fmt(self.duration)

    def save(self, *args, **kwargs):
        if (
            self.duration is None and
            self.file.file is not None
        ):
            with contextlib.closing(wave.open(self.file.file, 'r')) as wave_file:
                frames = wave_file.getnframes()
                rate = wave_file.getframerate()
                self.duration = timedelta(seconds=frames / float(rate))
                if kwargs.get('update_fields', None):
                    kwargs['update_fields'].append('duration')

        if not self.name:
            self.name = os.path.basename(self.file.name)
            if kwargs.get('update_fields', None):
                kwargs['update_fields'].append('name')

        super().save(*args, **kwargs)

    @property
    def size_str(self):
        if self.file.path is not None and os.path.exists(self.file.path):
            return sizeof_fmt(os.path.getsize(self.file.path))
        return ''

    def __str__(self):
        return self.name


class PlaybackTimeRangeManager(models.Manager):

    def scheduled_playlist(self):
        current_time = datetime.now()
        return self.get_queryset().filter(
            Q(day_of_week=PlaybackTimeRange.DayOfWeek(current_time)) &
            Q(start__lte=current_time.time()) &
            Q(end__gte=current_time.time())
        ).first()

    def last_scheduled_playlist(self):
        """
        Returns a 2-tuple where the first element is the start datetime of the
        next scheduled playback and the second element is the PlaybackTimeRange
        object.
        """
        current_time = datetime.now()
        dow = PlaybackTimeRange.DayOfWeek(current_time)
        earlier_this_week = self.get_queryset().filter(
            (Q(day_of_week=dow) & Q(end__lt=current_time.time())) |
            Q(day_of_week__lt=PlaybackTimeRange.DayOfWeek(current_time))
        ).order_by('-day_of_week').first()
        if earlier_this_week:
            return (
                datetime.combine(
                    current_time - timedelta(
                        days=dow.value - earlier_this_week.day_of_week.value
                    ), earlier_this_week.start
                ),
                earlier_this_week
            )
        later_last_week = self.get_queryset().filter(
            (Q(day_of_week=dow) & Q(end__gt=current_time.time())) |
            Q(day_of_week__gt=dow)
        ).order_by('-day_of_week').first()
        if later_last_week:
            return (
                datetime.combine(
                    current_time - timedelta(
                        days=dow.value + 7-later_last_week.day_of_week.value
                    ), later_last_week.start
                ),
                later_last_week
            )
        return None, None

    def next_scheduled_playlist(self):
        """
        Returns a 2-tuple where the first element is the start datetime of the
        next scheduled playback and the second element is the PlaybackTimeRange
        object.
        """
        current_time = datetime.now()
        dow = PlaybackTimeRange.DayOfWeek(current_time)
        later_this_week = self.get_queryset().filter(
            (Q(day_of_week=dow) & Q(start__gt=current_time.time())) |
            Q(day_of_week__gt=PlaybackTimeRange.DayOfWeek(current_time))
        ).order_by('day_of_week').first()
        if later_this_week:
            return (
                datetime.combine(
                    current_time + timedelta(
                        days=later_this_week.day_of_week.value - dow.value
                    ), later_this_week.start
                ),
                later_this_week
            )
        next_week = self.get_queryset().filter(
            (Q(day_of_week=dow) & Q(start__lt=current_time.time())) |
            Q(day_of_week__lt=dow)
        ).order_by('day_of_week').first()
        if next_week:
            return (
                datetime.combine(
                    current_time + timedelta(
                        days=(7-dow.value) + next_week.day_of_week.value
                    ), next_week.start
                ),
                next_week
            )
        return None, None


class PlaybackTimeRange(models.Model):

    objects = PlaybackTimeRangeManager()

    class DayOfWeek(IntEnumProperties, s('label', case_fold=True)):

        MONDAY    = 1, 'Monday'
        TUESDAY   = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY  = 4, 'Thursday'
        FRIDAY    = 5, 'Friday'
        SATURDAY  = 6, 'Saturday'
        SUNDAY    = 7, 'Sunday'

        def __str__(self):
            return self.label

        @classmethod
        def _missing_(cls, value):
            if isinstance(value, (date, datetime)):
                return cls(value.isoweekday())
            return super()._missing_(value)

    day_of_week = EnumField(DayOfWeek, unique=True)
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        blank=True
    )
    start = models.TimeField(db_index=True)
    end = models.TimeField(db_index=True)

    def save(self, *args, **kwargs):
        if not hasattr(self, 'playlist') or self.playlist is None:
            self.playlist = (
                PlaybackSettings.load().default_playlist or
                Playlist.objects.first()
            )
            if kwargs.get('update_fields', None):
                kwargs['update_fields'].append('playlist')

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.day_of_week.label}' \
               f'[{self.start.strftime("%I:%M %p")} - ' \
               f'{self.end.strftime("%I:%M %p")}] ' \
               f'({self.playlist.name})'

    class Meta:
        ordering = ['day_of_week', 'start']
        verbose_name_plural = 'Schedule'
        verbose_name = 'Schedule'
        constraints = [
            CheckConstraint(
                check=Q(start__lt=F('end')),
                name='%(app_label)s_%(class)s_start_lt_end'
            )
        ]


class ManualOverride(models.Model):

    class Operation(IntEnumProperties, s('label', case_fold=True)):

        PLAY = 0, 'Play'
        STOP = 1, 'Stop'

    operation = EnumField(Operation)
    timestamp = models.DateTimeField(
        db_index=True,
        default=datetime.now,
        null=False,
        blank=True
    )

    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not hasattr(self, 'playlist') or self.playlist is None:
            if self.operation is ManualOverride.Operation.PLAY:
                self.playlist = (
                        PlaybackSettings.load().default_playlist or
                        Playlist.objects.first()
                )
            else:
                self.playlist = getattr(
                    PlaybackTimeRange.objects.scheduled_playlist(),
                    'playlist',
                    Playlist.objects.first()
                )
        super().save(*args, **kwargs)

    @property
    def effective_playlist(self):
        return self.playlist or PlaybackSettings.load().default_playlist

    def __str__(self):
        return f'{self.operation.label} ' \
               f'{getattr(self.effective_playlist, "name", "")} ' \
               f'{self.timestamp}'

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

        override = ManualOverride.objects.filter(
            timestamp__lte=datetime.now()
        ).first()
        if (
            override and
            (datetime.now() - override.timestamp) >= timedelta(days=1)
        ):
            override = None

        scheduled = PlaybackTimeRange.objects.scheduled_playlist()
        if override is None:
            return getattr(scheduled, 'playlist', None)
        elif scheduled is None:
            # if we have an override but no currently scheduled playlist
            # that override may have occurred before the last scheduled
            # playlist, during it, or after it. Overrides only apply if they
            # occurred after the start of the last scheduled playlist
            if override.operation is override.Operation.PLAY:
                last_start, last_sched = PlaybackTimeRange.objects.last_scheduled_playlist()
                if last_sched is None or last_start < override.timestamp:
                    return override.playlist
            return None
        else:
            # if we have both an override and a currently scheduled playlist,
            # use the override if it is more recent than the start of the
            # scheduled playlist
            override_time = override.timestamp
            override_dow = PlaybackTimeRange.DayOfWeek(override_time)
            if (
                override_dow is not scheduled.day_of_week or
                override_time.time() < scheduled.start
            ):
                return scheduled.playlist
            elif override.operation is override.Operation.PLAY:
                return override.playlist
        return None

    def __str__(self):
        return 'Settings'

    class Meta:
        verbose_name_plural = 'Playback Settings'
        verbose_name = 'Playback Settings'
