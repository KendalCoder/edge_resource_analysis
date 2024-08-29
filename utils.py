import json
import pandas as pd
import matplotlib.pyplot as plt
from sage_data_client import query
import numpy as np

pd.set_option('mode.chained_assignment',None)


def get_data(vsn, start='-1h', end=''):
    if end != "":
        return query(
        start=start,
        end=end,
        filter={
            "name": "sys.scheduler.status.plugin.*",
            "vsn": vsn.upper(),
            }
        )
    else:
        return query(
        start=start,
        filter={
            "name": "sys.scheduler.status.plugin.*",
            "vsn": vsn.upper(),
            }
        )



def parse_events(df):
    v = []
    for _, row in df.iterrows():
        r = json.loads(row.value)
        r["timestamp"] = row.timestamp.isoformat()
        r["node"] = row["meta.node"]
        r["vsn"] = row["meta.vsn"]
        r["event"] = row["name"]
        v.append(r)
    return pd.read_json(json.dumps(v))


def fill_completion_failure(df):
    # Filter only events related to plugin execution
    launched = df[df.event.str.contains("launched")]
    completed = df[df.event.str.contains("complete")]
    failed = df[df.event.str.contains("failed")]
    # launched.loc[launched["k3s_pod_name"] == completed["k3s_pod_name"]]
    for index, p in launched.iterrows():
        found = completed[completed.k3s_pod_instance == p.k3s_pod_instance]
        if len(found) > 0:
            launched.loc[index, "completed_at"] = found.iloc[0].timestamp
            launched.loc[index, "execution_time"] = (found.iloc[0].timestamp - p.timestamp).total_seconds()
            launched.loc[index, "k3s_pod_node_name"] = found.iloc[0].k3s_pod_node_name
            launched.loc[index, "end_state"] = "completed"
        else:
            found = failed[failed.k3s_pod_instance == p.k3s_pod_instance]
            if len(found) > 0:
                launched.loc[index, "failed_at"] = found.iloc[0].timestamp
                launched.loc[index, "execution_time"] = (found.iloc[0].timestamp - p.timestamp).total_seconds()
                launched.loc[index, "reason"] = found.iloc[0].reason
                if "error_log" in found.iloc[0]:
                    launched.loc[index, "error_log"] = found.iloc[0]["error_log"]
                launched.loc[index, "k3s_pod_node_name"] = found.iloc[0].k3s_pod_node_name
                launched.loc[index, "end_state"] = "failed"
            else:
                launched.loc[index, "end_state"] = "unknown"
    return launched


def get_vsn_performance_data(vsn, start, end):
    return query(
        start=start,
        end=end,
        filter={
            "vsn": vsn.upper(),
            },
        bucket="grafana-agent"
    )


def calculate_cpu_utilization_from_cpuseconds(_df, new_t):
    new_row = _df.iloc[0]
    new_row.value = 0
    new_row.timestamp = new_t
    _df = pd.concat([new_row.to_frame().T, _df], ignore_index=True)
    _df["timestamp"] = pd.to_datetime(_df["timestamp"])
    _df["elapsed"] = _df.timestamp.diff().dt.total_seconds().cumsum()
    _df["cpu"] = _df.value.astype(float).diff().fillna(0) / _df.timestamp.diff().dt.total_seconds() * 100.
    return _df.loc[1:]

def is_gpu_requested(plugin_instance_record: pd.Series):
    if plugin_instance_record.plugin_selector is np.nan:
        return False

    selector = json.loads(plugin_instance_record.plugin_selector)
    
    if "resource.gpu" in selector and selector["resource.gpu"] == "true":
        return True
    return False

def convert_nodename_to_devicename(node_name: str) -> str:
    if "nx" in node_name:
        return "Jetson"
    elif "rpi" in node_name:
        return "RaspberryPi"