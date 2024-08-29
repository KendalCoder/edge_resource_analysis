#!/usr/bin/python3

import os
import logging
import argparse
from pathlib import Path

from tqdm import tqdm

from utils import *


def generate_metrics_from_instance(t: tqdm, run: pd.Series):
    instance = run.k3s_pod_instance
    device = convert_nodename_to_devicename(run.k3s_pod_node_name)
    gpu_required = is_gpu_requested(run)
    plugin_name = run.plugin_name
    vsn = run.vsn
    started = pd.to_datetime(run.timestamp)
    completed = pd.to_datetime(run.completed_at)
    extended_started = pd.to_datetime(run.timestamp) - pd.to_timedelta(1, unit='m')
    extended_completed = pd.to_datetime(run.completed_at) + pd.to_timedelta(1, unit='m')
    extended_started = extended_started.isoformat()
    extended_completed = extended_completed.isoformat()

    t.write(f'{instance}: Fetching data from cloud ranging from {extended_started} to {extended_completed}')
    perf_df = get_vsn_performance_data(vsn, extended_started, extended_completed)
    if len(perf_df) < 1:
        t.write(f'No record found for {instance}')
        return pd.DataFrame()

    container_perf_df = perf_df[perf_df["meta.container"]==plugin_name]
    container_cpu_perf_df = container_perf_df[container_perf_df["name"]=="container_cpu_usage_seconds_total"]
    t.write(f'{instance}: {len(container_cpu_perf_df)} CPU records found')
    if len(container_cpu_perf_df) < 1:
        cpu = pd.DataFrame([], columns=["timestamp", "cpu"])
        cpu["timestamp"] = pd.to_datetime(cpu["timestamp"], utc=True)
    else:
        cpu = calculate_cpu_utilization_from_cpuseconds(container_cpu_perf_df.copy(), started)[["timestamp", "cpu"]]
        cpu = cpu.sort_values(by="timestamp")

    container_mem_rss_perf_df = container_perf_df[container_perf_df["name"]=="container_memory_rss"]
    container_mem_workingset_perf_df = container_perf_df[container_perf_df["name"]=="container_memory_working_set_bytes"]
    t.write(f'{instance}: {len(container_mem_workingset_perf_df)} Memory workingset records found')
    if len(container_mem_workingset_perf_df) < 1:
        mem = pd.DataFrame([], columns=["timestamp", "mem"])
        mem["timestamp"] = pd.to_datetime(mem["timestamp"], utc=True)
    else:
        container_mem_workingset_perf_df["mem"] = container_mem_workingset_perf_df["value"].values + container_mem_rss_perf_df["value"].values
        mem = container_mem_workingset_perf_df[["timestamp", "mem"]]
    try:
        mem = mem.sort_values(by="timestamp")
        merged_instance = pd.merge_asof(cpu[["timestamp", "cpu"]], mem[["timestamp", "mem"]], on="timestamp")
    except ValueError as ex:
        t.write(f'{instance}: ERROR="{ex}" DATA={cpu}')
        return pd.DataFrame()

    if "meta.sensor" not in perf_df.columns:
        t.write(f'{instance}: meta.sensor field not found. Unable to retrive power measurements')
        pow = pd.DataFrame([], columns=["timestamp", "sys_power", "cpugpu_power"])
        pow["timestamp"] = pd.to_datetime(pow["timestamp"], utc=True)
        merged_instance = pd.merge_asof(merged_instance, pow, on="timestamp")
    else:
        tegra_total_power = perf_df[(perf_df["name"] == "tegra_wattage_current_milliwatts") & (perf_df["meta.sensor"] == "vdd_in")]
        t.write(f'{instance}: {len(tegra_total_power)} tegra power metric records found')
        tegra_total_power = tegra_total_power.rename({"value": "sys_power"}, axis="columns")
        tegra_total_power = tegra_total_power.sort_values(by="timestamp")
        merged_instance = pd.merge_asof(merged_instance, tegra_total_power[["timestamp", "sys_power"]], on="timestamp")

        tegra_cpugpu_power = perf_df[(perf_df["name"] == "tegra_wattage_current_milliwatts") & (perf_df["meta.sensor"] == "vdd_cpu_gpu_cv")]
        t.write(f'{instance}: {len(tegra_total_power)} tegra cpugpu power metric records found')
        tegra_cpugpu_power = tegra_cpugpu_power.rename({"value": "cpugpu_power"}, axis="columns")
        tegra_cpugpu_power = tegra_cpugpu_power.sort_values(by="timestamp")
        merged_instance = pd.merge_asof(merged_instance, tegra_cpugpu_power[["timestamp", "cpugpu_power"]], on="timestamp")

    # Merging all metrics
    merged_instance["plugin_instance"] = instance
    merged_instance["device"] = device
    merged_instance["gpu_requested"] = gpu_required
    merged_instance['timestamp'] = merged_instance['timestamp'].map(lambda x: x.isoformat())
    t.write(f'{instance}: Generated {len(merged_instance)} records. Done.')
    return merged_instance


def main(args):
    input_path = Path(args.input)
    output_dir = input_path.parents[0]
    logging.info(f'Reading {input_path}')
    df = pd.read_csv(input_path)

    logging.info(f'Output dir is {output_dir}')

    logging.info("We consider only successfully completed runs and not the ones failed or unknown")
    completed_runs = df[df["end_state"] == "completed"]
    logging.info(f'Completed plugin runs by {completed_runs.groupby("plugin_task").size()}')

    # logging.info("Sorting the runs by plugin_name")
    # completed_runs = completed_runs.sort_values(by="plugin_name")

    # total_iteration = len(completed_runs)
    # t = tqdm(range(total_iteration))
    # run = completed_runs[completed_runs["k3s_pod_instance"] == "avian-diversity-monitoring-RU9ugV"]
    # df = generate_metrics_from_instance(t, run)
    # df.to_csv("test.csv", index=False)
    for plugin_name, runs in completed_runs.groupby("plugin_name"):
        logging.info(f'Generating metrics for {plugin_name}')
        plugin_df = pd.DataFrame()
        plugin_output_path = output_dir.joinpath(f'{plugin_name}.csv')
        if plugin_output_path.exists() and args.resume:
            logging.info(f'{plugin_output_path} already exists. --resume is enabled. Skipping.')
            continue

        total_iteration = len(runs)
        t = tqdm(range(total_iteration))
        # for _, run in runs.iterrows():
        for i in t:
            run = runs.iloc[i]
            run_df = generate_metrics_from_instance(t, run)
            plugin_df = pd.concat([plugin_df, run_df])
        plugin_df.to_csv(plugin_output_path, index=False)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", dest="debug",
        action="store_true",
        help="Enable debugging")
    parser.add_argument(
        "-i", "--input", dest="input",
        action="store", required=True,
        help="Input plugin list in csv")
    parser.add_argument(
        "--resume", dest="resume",
        action="store_true",
        help="Skip if plugin data already exists")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    exit(main(args))
