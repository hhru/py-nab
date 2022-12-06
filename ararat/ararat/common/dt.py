from datetime import datetime

from pytz import timezone

MSK_TIMEZONE = timezone("Europe/Moscow")
UTC_TIMEZONE = timezone("UTC")


def datetime_now(tz=UTC_TIMEZONE):
    now = datetime.now(tz)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def is_naive(dt: datetime) -> bool:
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def as_msk(dt: datetime) -> datetime:
    if is_naive(dt):
        dt = timezone("UTC").localize(dt)

    return dt.astimezone(MSK_TIMEZONE)


def get_dt_millis(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)
