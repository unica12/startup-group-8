from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

REPORTING_ZONE = ZoneInfo("Europe/Moscow")


def reporting_day(moment: datetime | None = None) -> date:
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(REPORTING_ZONE).date()


def utc_period_start(day: date) -> datetime:
    return datetime.combine(day, time.min, REPORTING_ZONE).astimezone(timezone.utc).replace(tzinfo=None)
