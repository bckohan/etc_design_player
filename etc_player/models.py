from django.db import models
from django_enum import EnumField
from enum_properties import IntEnumProperties, s
from django.core.cache import cache


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

    def __str__(self):
        return self.name


class PlaybackTimeRange(models.Model):

    class DayOfWeek(IntEnumProperties, s('label', case_fold=True)):

        SUNDAY    = 0, 'Sunday'
        MONDAY    = 1, 'Monday'
        TUESDAY   = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY  = 4, 'Thursday'
        FRIDAY    = 5, 'Friday'
        SATURDAY  = 6, 'Saturday'

    day_of_week = EnumField(DayOfWeek, unique=True)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return f'{self.day_of_week.label} {self.start} - {self.end}'

    class Meta:
        ordering = ['day_of_week', 'start']
        verbose_name_plural = 'Schedule'
        verbose_name = 'Schedule'


class PlaybackSettings(SingletonModel):

    volume = models.PositiveSmallIntegerField(null=False, default=100)

    class Meta:
        verbose_name_plural = 'Playback Settings'
        verbose_name = 'Playback Settings'
