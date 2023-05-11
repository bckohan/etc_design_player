# Generated by Django 4.2.1 on 2023-05-10 06:43

from django.db import migrations, models
import django.db.models.deletion
import django_enum.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PlaybackSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('volume', models.PositiveSmallIntegerField(default=100)),
            ],
            options={
                'verbose_name': 'Playback Settings',
                'verbose_name_plural': 'Playback Settings',
            },
        ),
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Wave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/')),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('length', models.DurationField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PlaylistWave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField()),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='etc_player.playlist')),
                ('wave', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='etc_player.wave')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='playlist',
            name='waves',
            field=models.ManyToManyField(through='etc_player.PlaylistWave', to='etc_player.wave'),
        ),
        migrations.CreateModel(
            name='PlaybackTimeRange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', django_enum.fields.EnumPositiveSmallIntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')], unique=True)),
                ('start', models.TimeField()),
                ('end', models.TimeField()),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='etc_player.playlist')),
            ],
            options={
                'ordering': ['day_of_week', 'start'],
            },
        ),
    ]