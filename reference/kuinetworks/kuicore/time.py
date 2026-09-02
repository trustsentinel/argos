from datetime import datetime

def unix_time_millis(dt):
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000.0)

def now():
    return datetime.now()

def timestamp_today():
    now = datetime.now()
    return int(datetime(now.year, now.month, now.day, 0, 0).timestamp())
