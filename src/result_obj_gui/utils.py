from datetime import datetime
from datetime import timezone

import justpy as jp

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


def bytes_to_readable_str(size):
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if size < 1024.0:
            if unit == "B":
                return "%d %s" % (size, unit)
            return "%3.1f %s" % (size, unit)

        size /= 1024.0

    return size


def _create_section(div_content, name):
    section_id = name.replace(" ", "-")
    section = jp.Section(
        a=div_content,
        id=section_id,
        classes="overflow-hidden rounded-lg shadow-md bg-white hover:shadow-xl transition-shadow duration-300 ease-in-out p-4 mt-4",
    )
    section.add(jp.H3(classes="text-2xl font-semibold pb-3", text=name))

    return section
