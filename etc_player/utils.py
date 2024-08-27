import logging
import subprocess
from datetime import datetime, timedelta

from django.conf import settings

last_restart = None


logger = logging.getLogger("etc_player")


def restart_audio():
    # throttle restarts - signals might result in lots of calls to it - ok
    # since call to this is wrapped in a transaction.on_commit so should only
    # happen once DB state is consistent with the end of the request
    global last_restart
    if last_restart is None or (datetime.now() - last_restart) > timedelta(seconds=1):
        subprocess.run(settings.RESTART_COMMAND.split())
        last_restart = datetime.now()


def set_volume(volume):
    cmd = settings.VOLUME_COMMAND.format(volume=max(0, min(100, int(volume)))).split()
    try:
        subprocess.run(cmd)
    except Exception:
        logger.exception("Error setting volume")


def sizeof_fmt(num, suffix="B"):
    if num is not None:
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"
    return ""


def duration_fmt(duration):
    dstr = ""
    if duration:
        tot_seconds = int(duration.total_seconds())
        minutes = tot_seconds // 60
        seconds = tot_seconds % 60
        if minutes > 0:
            dstr += f"{minutes} minutes"
        if seconds > 0:
            dstr += f'{", " if dstr else ""}{seconds} seconds'
    return dstr
