#!/usr/bin/python3

import logging
import argparse

from utils import *

@click.group()
def cli():
    pass

@cli.command()
@click.option("-v", "--vsn", required=True, type=str, help="VSN of the node.")
@click.option("-s", "--start", required=True, help="Start time of the query in UTC, e.g. 1h, 10d, 2024-01-01T00:00:00Z")
@click.option("-e", "--end", default="", help="End time of the query in UTC, e.g. 1h, 10d, 2024-01-02T00:00:00Z")
@click.option("-o", "--output", type=Path, default=Path("jobs.csv"), help="Path to save the downloaded data. Default is jobs.csv")
@click.option("-b", "--bulk", is_flag=True, default=False, help="Enable downloading data in splits. This helps lowering server-side loads when downloading with a large time window such as months. The default time window in the split is day.")
def job(vsn, start, end, output, bulk):
    start_t, err = parse_time(start)
    end_t, err = parse_time(end)
    logging.info(f'Query ranges from {start_t} to {end_t}.')
    if bulk:
        logging.info("Bulk download enabled.")
        df = download_bulk_data(
            DOWNLOAD_TYPE_JOB,
            download_scheduler_event,
            vsn,
            start_t,
            end_t)
    else:
        df = download_scheduler_event(vsn, start_t, end_t)

    logging.info(f'{len(df)} records found.')
    if len(df) == 0:
        logging.info(f'Query {vsn} {start_t} {end_t} returned 0 records.')
        return 0

    logging.info(f'Parsing the records.')
    out_df = generate_job_records(df)
    out_df.to_csv(output, index=False)
    logging.info(f'Created {output}. Done.')


@cli.command()
@click.option("-i", "--input", required=True, type=Path, default=Path("jobs.csv"), help="Path to the job list in CSV. Default is ./jobs.csv")
@click.option("-r", "--resume", is_flag=True, default=False, help="Skip downloading if exists locally. It is useful when resuming downloading from where it left off.")
@click.option("-o", "--output-dir", type=Path, default=Path("./"), help="Path to save the downloaded data. Default is the current directory.")
def perf(input, resume, output_dir):
    logging.info(f'Reading job data from {input}.')
    df = pd.read_csv(input)

    logging.info(f'Output directory is {output_dir}.')

    logging.info("We consider only successfully completed runs, not the ones that are failed or unknown")
    completed_runs = df[df["end_state"] == "completed"]
    logging.info(f'{len(completed_runs)} completed runs found.')
    logging.info(f'Completed runs by plugin name are {completed_runs.groupby("plugin_task").size()}')

    # logging.info("Sorting the runs by plugin_name")
    # completed_runs = completed_runs.sort_values(by="plugin_name")

    for plugin_name, runs in completed_runs.groupby("plugin_name"):
        logging.info(f'Downloading metrics for {plugin_name}')
        plugin_df = pd.DataFrame()
        plugin_output_path = output_dir.joinpath(f'{plugin_name}.csv')
        if plugin_output_path.exists() and resume:
            logging.info(f'{plugin_output_path} already exists. --resume is enabled. Skipping.')
            continue

        total_iteration = len(runs)
        t = tqdm(range(total_iteration))
        for i in t:
            run = runs.iloc[i]
            run_df = generate_metrics_from_instance(t, run)
            plugin_df = pd.concat([plugin_df, run_df])
        plugin_df.to_csv(plugin_output_path, index=False)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    cli()