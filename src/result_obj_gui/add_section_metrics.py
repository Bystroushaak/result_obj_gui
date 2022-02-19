import justpy as jp

from result_obj.metrics import Metric
from result_obj.metrics import MetricInfo

from utils import _create_section


def add_metrics_section(div_content, db):
    section_metrics = _create_section(div_content, "Metrics")

    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT name, type FROM Metrics")
    metrics_list = cursor.fetchall()

    if not metrics_list:
        return None

    metrics_value = {}
    metrics_counters = {}
    metrics_start_stop = {}
    for metric in metrics_list:
        metric_name = metric["name"]
        metric_type = metric["type"]

        metrics_generator = _read_metrics(db, metric_name, metric_type)
        if metric_type == Metric.TYPE_VALUE:
            metrics_value[metric_name] = metrics_generator
        elif metric_type == Metric.TYPE_INCREMENT:
            metrics_counters[metric_name] = metrics_generator
        elif metric_type == Metric.TYPE_START:
            metrics_start_stop[metric_name] = metrics_generator

    for metric_name, metric_data in metrics_value.items():
        _add_chart_values(metric_data, metric_name, section_metrics)
    for metric_name, metric_data in metrics_counters.items():
        _add_chart_counter(metric_data, metric_name, section_metrics)
    for metric_name, metric_data in metrics_start_stop.items():
        _add_chart_start_stop(metric_data, metric_name, section_metrics)

    return section_metrics


def _read_metrics(db, metric_name, metric_type):
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
