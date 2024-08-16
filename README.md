# Jupyter notebooks to analyze on computing resource on the edge

This repository holds a number of Jupyter notebooks that analyze computing resources and application performance using data obtained from Waggle nodes. You will need to install [sage_data_client](https://pypi.org/project/sage-data-client/) in order to run the notebooks on your computer.

## How to use

Step 1. Download runs of edge applications from Waggle cloud.

```bash
# Querying application runs from the W020 Waggle node in the last hour
python3 get-jobs.py --vsn W020 --start 1h
```

jobs.csv will be created and show the list of application executions on the node during the time window.

Step 2. Place it in a file structure so that you can re-run the same over multiple nodes for multiple time windows. In this example, we put it in "data/W020"

```bash
mkdir -p data/W020
mv jobs.csv data/W020
```

Step 3. Download performance metrics from the Waggle cloud and generate the resource footprint of the applications

```bash
python3 generate.py -i data/W020/jobs.csv
```

In the directory "data/W020" there will be APPLICATION_NAME.csv files representing their runs on the node. Those csv files will then be used to understand the resource profile of applications.

## Output format

Each APPLICATION_NAME.csv file has a header,
- timestamp: timestamp in UTC of the measurement
- cpu: CPU utilization of the application. The unit is percentage. 100 percentage means 1 logical CPU core. If the value is 150, this means the application was using 1.5 CPU cores.
- mem: Memory usage of the application in bytes and is calculated by summing workingset memory and swap memory of the application.
- sys_power: System-wide power metric in milliwatts. This represents the power being consumed by the device.
- cpugpu_power: System-wide power metric in milliwatts. This represents the power being consumed by all available CPU and GPU cores. This does not represent the amount of power the application uses, instead represent the amount consumed by all other applications and OS at the time of measurement.
- plugin_instance: A unique name of the application for a particular run. If there are 5 different plugin instances, then it means that the application ran 5 times within the time that was used to query this data.

__NOTE: the header may be changed as this tool is being actively developed.__

Each metric represents its instaneous value measured from the system in the node. For example, 50.5 in the cpu column means that the CPU utilization at the timestamp (i.e., when the value was measured) was 50.5.

## Developer Notes
- Because we can't measure GPU utilization reliably when plugins run AI inference for a very short time, we could infer GPU utilization from GPU_U + CPU_U = VDD_CPU_GPU_CV.