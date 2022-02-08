from datetime import datetime
from datetime import timezone


LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


def str_from_ts(ts):
    dt_object = datetime.fromtimestamp(float(ts))
    local_tz_dt = dt_object.astimezone(LOCAL_TIMEZONE)

    return local_tz_dt.strftime("%Y-%m-%d %H:%M:%S")


def iso_str_from_ts(ts):
    dt_object = datetime.fromtimestamp(float(ts))
    local_tz_dt = dt_object.astimezone(LOCAL_TIMEZONE)

    return local_tz_dt.isoformat()


def html_from_ts(ts):
    dt_object = datetime.fromtimestamp(float(ts))
    local_tz_dt = dt_object.astimezone(LOCAL_TIMEZONE)

    short_str = local_tz_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    iso_str = local_tz_dt.isoformat()

    return f'<em title="{iso_str}">{short_str[:-4]}</em>'
