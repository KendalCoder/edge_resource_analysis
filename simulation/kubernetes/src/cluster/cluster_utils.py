import os
from string import Template
from pathlib import Path

import yaml

clsuter_utils_path = os.path.dirname(os.path.abspath(__file__))
template_path = Path(clsuter_utils_path) / "template"

def create_node(name: str, device: str):
    device_template_path = template_path / f'{device}.yaml.tmpl'
    with open(device_template_path, "r") as file:
        t = Template(file.read())
        r = t.substitute({
            "NAME": name.lower(),
        })
    return yaml.safe_load(r)


def create_pod(workload: dict):
    # Copy the workload to avoid modifying the original workload
    _workload = workload.copy()
    labels = _workload.pop("LABELS", {})

    workload_template_path = template_path / "pod.yaml.tmpl"
    default = {
        "NAME": "mypod",
        "REQUEST_CPU": "100m",
        "REQUEST_MEMORY": "1Mi",
    }
    default.update(_workload)
    with open(workload_template_path, "r") as file:
        t = Template(file.read())
        r = t.substitute(default)
    pod = yaml.safe_load(r)

    # Add any additional labels
    existing_labels = pod["metadata"].get("labels", {})
    existing_labels.update(labels)
    pod["metadata"]["labels"] = existing_labels
    return pod

def convert_to_bytes(value):
    """
    Convert a value to bytes.
    """
    if value[-2:] == 'Mi':
        return int(value[:-2]) * 1024 * 1024
    elif value[-2:] == 'Gi':
        return int(value[:-2]) * 1024 * 1024 * 1024
    else:
        return int(value)
    
def convert_to_millicores(value):
    """
    Convert a value to millicores.
    """
    if isinstance(value, int):
        return int(value) * 1000
    if value[-1] == 'm':
        return int(value[:-1])
    elif value[-1] == 'n':
        return int(value[:-1]) / 1000000
    else:
        return int(value) * 1000
