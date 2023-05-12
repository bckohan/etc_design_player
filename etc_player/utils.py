import subprocess
from django.conf import settings
from datetime import timedelta, datetime

last_restart = None


def restart_audio():
    # throttle these - signals might result in lots of calls to it
    global last_restart
    if (
        last_restart is None or
        (datetime.now() - last_restart) > timedelta(seconds=1)
    ):
        subprocess.run(settings.RESTART_COMMAND.split())
        last_restart = datetime.now()


def set_volume(volume):
    cmd = settings.VOLUME_COMMAND.format(
        volume=max(0, min(100, int(volume)))
    ).split()
    subprocess.run(cmd)


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def duration_fmt(timedelta):
    dstr = ''
    tot_seconds = int(timedelta.total_seconds())
    minutes = tot_seconds // 60
    seconds = tot_seconds % 60
    if minutes > 0:
        dstr += f'{minutes} minutes, '
    else:
        dstr += f'{seconds} seconds'
    return dstr
