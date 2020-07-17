from datetime import datetime, timedelta


# --- Date formatter:
__FMT_SMALL = 'le %d/%m/%y à %Hh%M'     # Small format
__FMT_NORMAL = '%A %d %B %Y à %Hh%M'    # Normal format


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = datetime.now().timestamp()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def delta_formatter(delta):
    seconds = abs(delta.seconds)
    future = delta.seconds < 0

    if seconds < 5:
        return 'maintenant'

    if seconds > 3600:
        hours = seconds // 3600
        s = '{} heure{}'.format(hours, 's' if hours > 1 else '')
    elif seconds > 60:
        minutes = seconds // 60
        s = '{} minute{}'.format(minutes, 's' if minutes > 1 else '')
    else:
        s = '{} seconde{}'.format(seconds, 's' if seconds > 1 else '')

    return '{} {}'.format('dans' if future else 'il y a', s)


def date_formatter(value, small=True):
    if not isinstance(value, datetime):
        return value

    if value.tzinfo is None:
        value = datetime_from_utc_to_local(value)

    now = datetime.now()
    now = now - timedelta(microseconds=now.microsecond)
    delta = now - value
    if delta.days == 0:
        return delta_formatter(delta)
    else:
        return value.strftime(__FMT_SMALL if small else __FMT_NORMAL)


# --- File size formatter
def file_size_formatter(size):
    if size > pow(1024, 2):
        return '{:.1f} Mio'.format(size / pow(1024, 2))
    elif size > pow(1024, 1):
        return '{:.1f} Kio'.format(size / pow(1024, 1))
    else:
        return '{} o'.format(size)


# filters
filters = {
    'date_formatter': date_formatter,
    'file_size_formatter': file_size_formatter
}
