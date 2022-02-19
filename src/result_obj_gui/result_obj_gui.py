#! /usr/bin/env python3
import sqlite3
import argparse

import justpy as jp

from result_obj.metrics import Metric
from result_obj.metrics import MetricInfo

from utils import str_from_ts
from utils import html_from_ts
from utils import iso_str_from_ts
from utils import bytes_to_readable_str


def generate_report(sqlite_path):
    wp = jp.WebPage(delete_flag=False)
    div_container = jp.Div(
        a=jp.Div(a=wp, classes="md:container md:mx-auto"),
        classes="min-h-screen flex flex-row bg-gray-100",
    )

    db = sqlite3.connect(sqlite_path)
    db.row_factory = sqlite3.Row

    div_content = jp.Div(classes="p-3 w-full")
    sections_iterator = _generate_sections(div_content, db)
    div_navigation = _add_navigation(sections_iterator)

    div_container.add(div_navigation)
    div_container.add(div_content)

    return lambda: wp


def _generate_sections(div_content, db):
    _add_title_section(div_content)

    yield _add_overview_section(div_content, db)
    yield _add_metrics_section(div_content, db)
    yield _add_status_section(div_content, db)
    yield _add_restore_points_section(div_content, db)
    yield _add_result_section(div_content, db)
    yield _add_logs_section(div_content, db)


def _add_title_section(div_content):
    section_title = jp.Section(a=div_content)
    h1 = jp.H1(a=section_title, classes="text-2xl p-4 text-center")
    h1.add(jp.Code(text="result_obj"))
    h1.add(jp.Span(text=" info"))


def _add_overview_section(div_content, db):
    section_overview = _create_section(div_content, "Overview")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM Metadata ORDER BY timestamp")
    metadata_list = cursor.fetchall()

    metadata_start = metadata_list[0]
    metadata_end = metadata_list[-1]

    start_ts = metadata_start["timestamp"]
    end_ts = metadata_end["timestamp"]
    jp.P(
        a=section_overview,
        inner_html=f"Started: {html_from_ts(start_ts)}.",
    )
    jp.P(
        a=section_overview,
        inner_html=f"Ended: {html_from_ts(end_ts)}.",
    )
    jp.P(
        a=section_overview,
        inner_html=f"Duration: <em>{end_ts - start_ts:.2}</em> seconds.",
    )
    jp.P(
        a=section_overview,
        text=f"Command: {metadata_start['argv']}",
    )
    jp.P(
        a=section_overview,
        text=f"Directory: {metadata_start['pwd']}",
    )

    cursor.execute("SELECT key, value FROM MetadataEnvVars ORDER BY key")
    env_var_list = cursor.fetchall()

    jp.H2(a=section_overview, text=f"Env variables", classes="text-l font-semibold")

    table_options = {
        "defaultColDef": {
            "filter": True,
            "sortable": True,
            "resizable": True,
            "headerClass": "font-bold",
            "wrapText": True,
        },
        "columnDefs": [
            {"headerName": "Name", "field": "key"},
            {
                "headerName": "Value",
                "field": "value",
                "minWidth": 1050,
                "autoHeight": True,
                "editable": True,
            },
        ],
        "rowHeight": 120,
        "rowData": [],
    }
    table = jp.AgGrid(
        a=section_overview, options=table_options, style="height: 400px; margin: 0.25em"
    )
    table.options.columnDefs[1].cellStyle = "white-space: normal;"
    for env_var in env_var_list:
        table.options.rowData.append({"key": env_var["key"], "value": env_var["value"]})

    return section_overview


def _add_metrics_section(div_content, db):
    section_metrics = _create_section(div_content, "Metrics")

    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT name, type FROM Metrics")
    metrics_list = cursor.fetchall()

    if not metrics_list:
        return None

    def _read_metrics(metric_name, metric_type):
        cursor = db.cursor()
        if metric_type == Metric.TYPE_START:
            cursor.execute(
                "SELECT * FROM Metrics WHERE name=? AND (type=? OR type=?)",
                (metric_name, Metric.TYPE_START, Metric.TYPE_STOP)
            )
        else:
            cursor.execute(
                "SELECT * FROM Metrics WHERE name=? AND type=?",
                (metric_name, metric_type)
            )

        empty_dict = {}
        for metric in cursor.fetchall():
            m = MetricInfo(metric["type"], metric_name, empty_dict, metric["value"])
            m.timestamp = metric["timestamp"]
            yield m

    metrics_start_stop = {}
    metrics_counters = {}
    metrics_value = {}
    for metric in metrics_list:
        metric_name = metric["name"]
        metric_type = metric["type"]

        metrics_generator = _read_metrics(metric_name, metric_type)
        if metric_type == Metric.TYPE_START:
            metrics_start_stop[metric_name] = metrics_generator
        if metric_type == Metric.TYPE_INCREMENT:
            metrics_counters[metric_name] = metrics_generator
        if metric_type == Metric.TYPE_VALUE:
            metrics_value[metric_name] = metrics_generator

    for metric_name, metric_data in metrics_start_stop.items():
        _add_chart_start_stop(metric_data, metric_name, section_metrics)
    for metric_name, metric_data in metrics_counters.items():
        _add_chart_counter(metric_data, metric_name, section_metrics)
    for metric_name, metric_data in metrics_value.items():
        _add_chart_values(metric_data, metric_name, section_metrics)

    return section_metrics


def _add_chart_start_stop(metric_data, metric_name, section_metrics):
    y_axis = []
    x_axis = []
    start_ts = None
    for cnt, metric_info in enumerate(sorted(metric_data, key=lambda x: x.timestamp)):
        # make zero the default
        if cnt == 0:
            y_axis.append(metric_info.timestamp * 1000 - 1)
            x_axis.append(0)

        if metric_info.type == Metric.TYPE_START:
            x_axis.append(metric_info.timestamp)
            start_ts = metric_info.timestamp
        else:
            if not x_axis:  # prevent showing stop metric before start
                continue

            time_diff = metric_info.timestamp - start_ts
            x_axis[-1] = time_diff
            x_axis.append(time_diff)

            # default back to zero
            y_axis.append(metric_info.timestamp * 1000 + 1)
            x_axis.append(0)

        y_axis.append(metric_info.timestamp * 1000)

    my_chart_def = {
        "title": {
            "text": metric_name
        },
        "xAxis": {
            "type": 'datetime'
        },
        "yAxis": {
            "title": {
                "text": 'Seconds'
            }
        },
        "series": [{
            "name": 'How long the start/stop took',
            "data": list(zip(y_axis, x_axis))
        }]
    }
    my_chart = jp.HighCharts(a=section_metrics, classes='m-2 p-2 border')
    my_chart.options = my_chart_def


def _add_chart_counter(metric_data, metric_name, section_metrics):
    y_axis = []
    x_axis = []
    counter = 0
    for metric_info in metric_data:
        y_axis.append(metric_info.timestamp * 1000)
        x_axis.append(counter)
        counter += 1

    my_chart_def = {
        "title": {
            "text": metric_name
        },
        "xAxis": {
            "type": 'datetime'
        },
        "yAxis": {
            "title": {
                "text": 'Hits'
            }
        },
        "series": [{
            "name": 'Hit increment',
            "data": list(zip(y_axis, x_axis))
        }]
    }
    my_chart = jp.HighCharts(a=section_metrics, classes='m-2 p-2 border')
    my_chart.options = my_chart_def


def _add_chart_values(metric_data, metric_name, section_metrics):
    y_axis = []
    x_axis = []
    for metric_info in metric_data:
        y_axis.append(metric_info.timestamp * 1000)
        x_axis.append(metric_info.value)

    my_chart_def = {
        "title": {
            "text": metric_name
        },
        "xAxis": {
            "type": 'datetime'
        },
        "yAxis": {
            "title": {
                "text": 'Value'
            }
        },
        "series": [{
            "name": 'Numeric value',
            "data": list(zip(y_axis, x_axis))
        }]
    }
    my_chart = jp.HighCharts(a=section_metrics, classes='m-2 p-2 border')
    my_chart.options = my_chart_def


def _add_status_section(div_content, db):
    section_status = _create_section(div_content, "Status messages")

    cursor = db.cursor()
    cursor.execute("SELECT timestamp, status FROM StatusHistory ORDER BY timestamp")
    status_list = cursor.fetchall()

    if not status_list:
        return None

    height = 400
    if len(status_list) > 15:
        height = 1200

    table_options = {
        "defaultColDef": {
            "filter": True,
            "sortable": True,
            "resizable": True,
            "headerClass": "font-bold",
            "wrapText": True,
        },
        "columnDefs": [
            {"headerName": "Time", "field": "time"},
            {
                "headerName": "Status",
                "field": "status",
                "minWidth": 1050,
                "autoHeight": True,
                "editable": True,
            },
        ],
        "rowHeight": 120,
        "rowData": [],
        "pagination": True,
        "paginationPageSize": 40,
    }
    table = jp.AgGrid(
        a=section_status,
        options=table_options,
        style=f"height: {height}px; margin: 0.25em",
    )
    for status_data in status_list:
        table.options.rowData.append(
            {
                "time": iso_str_from_ts(status_data["timestamp"]),
                "status": status_data["status"],
            }
        )

    return section_status


def _add_restore_points_section(div_content, db):
    section_restore_points = _create_section(div_content, "Restore points")

    cursor = db.cursor()
    cursor.execute("SELECT timestamp, type, restore_data FROM RestorePoint")
    restore_points = cursor.fetchall()

    if not restore_points:
        return None

    for cnt, rp in enumerate(restore_points):
        _read_pickled_obj_info(
            section_restore_points,
            "Restore point",
            rp["timestamp"],
            rp["type"],
            rp["restore_data"],
        )
        if cnt < len(restore_points) - 1:
            jp.P(a=section_restore_points, inner_html="&nbsp;")

    return section_restore_points


def _add_result_section(div_content, db):
    section_result = _create_section(div_content, "Result")

    cursor = db.cursor()
    cursor.execute("SELECT timestamp, type, result FROM Result")
    result = cursor.fetchone()

    if not result:
        return None

    _read_pickled_obj_info(
        section_result, "Result", result["timestamp"], result["type"], result["result"]
    )

    return section_result


def _read_pickled_obj_info(section, name, added, data_type, data):
    jp.P(a=section, inner_html=f"{name} stored: {html_from_ts(added)}")
    jp.P(a=section, inner_html=f"{name} type: {data_type}")

    result_len = len(data)
    result_size = bytes_to_readable_str(result_len)
    jp.P(a=section, inner_html=f"{name} size: {result_size}")

    # TODO: convert to enum later
    if result_len < 1024 or data_type != "cpython_pickle":
        jp.P(a=section, text="Raw data:")
        jp.P(a=section, text=data)


def _add_logs_section(div_content, db):
    section_logs = _create_section(div_content, "Logs")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM Logs ORDER BY created")
    logs_list = cursor.fetchall()

    if not logs_list:
        return None

    table_options = {
        "defaultColDef": {
            "filter": True,
            "sortable": True,
            "resizable": True,
            "headerClass": "font-bold",
            "wrapText": True,
        },
        "columnDefs": [
            {"headerName": "Created", "field": "created"},
            {"headerName": "Level", "field": "levelname"},
            {
                "headerName": "Message",
                "field": "msg",
                # "minWidth": 1050,
                "autoHeight": True,
                "editable": True,
            },
            {"headerName": "Filename", "field": "filename"},
            {"headerName": "Line", "field": "lineno"},
            {"headerName": "Function", "field": "funcname"},
            {"headerName": "Name", "field": "name"},
            {"headerName": "Module", "field": "module"},
            {"headerName": "Path", "field": "pathname"},
            {"headerName": "Process", "field": "process"},
            {"headerName": "Process name", "field": "processName"},
            {"headerName": "Thread ID", "field": "thread"},
            {"headerName": "Thread name", "field": "threadName"},
        ],
        "rowHeight": 120,
        "pagination": True,
        "paginationPageSize": 40,
        "rowData": [],
    }

    height = 400
    if len(logs_list) > 15:
        height = 1200

    table = jp.AgGrid(
        a=section_logs,
        options=table_options,
        style=f"height: {height}px; margin: 0.25em",
    )
    for log in logs_list:
        table.options.rowData.append(
            {
                "created": iso_str_from_ts(log["created"]),
                "levelname": log["levelname"],
                "msg": log["msg"],
                "filename": log["filename"],
                "lineno": log["lineno"],
                "funcname": log["funcName"],
                "module": log["module"],
                "name": log["name"],
                "pathname": log["pathname"],
                "process": log["process"],
                "processName": log["processName"],
                "thread": log["thread"],
                "threadName": log["threadName"],
            }
        )

    return section_logs


def _create_section(div_content, name):
    section_id = name.replace(" ", "-")
    section = jp.Section(
        a=div_content,
        id=section_id,
        classes="overflow-hidden rounded-lg shadow-md bg-white hover:shadow-xl transition-shadow duration-300 ease-in-out p-4 mt-4",
    )
    section.add(jp.H3(classes="text-xl font-semibold pb-3", text=name))

    return section


def _add_navigation(items):
    div = jp.Div()
    div_ul_container = jp.Div(
        a=div,
        classes="sticky top-0 mt-20 w-32 pl-3 pt-2 ml-2 text-sm rounded-lg shadow-md bg-white",
    )

    ul = jp.Ul(a=div_ul_container, classes="nav")

    for section in items:
        if not section:
            continue

        link = "#" + section.id
        name = section.components[0].text

        li = jp.Li(a=ul, classes="py-1")
        jp.A(a=li, classes="nav-link", href=link, text=name)  # , scroll=True

    return div


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Web interface for the `result_obj` project \
                       https://github.com/Bystroushaak/result_obj"""
    )
    parser.add_argument("SQLITE", help="Path to the SQLite generated by `obj_result`.")
    args = parser.parse_args()

    jp.justpy(generate_report(args.SQLITE))
