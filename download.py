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
@click.option("-b", "--bulk", is_flag=True, default=False, help="Enable downloading data in splits. This helps lowering server-side loads when downloading with a large time window such as months. The default time window in the split is day.")
def job(vsn, start, end, bulk):
    start_t, err = parse_time(start)
    end_t, err = parse_time(end)
    if bulk:
        df = download_bulk_data(
            DOWNLOAD_TYPE_JOB,
            download_scheduler_event,
            vsn,
            start_t,
            end_t)
    else:
        df = download_scheduler_event(vsn, start_t, end_t)

    logging.info(f'{len(df)} records found')
    if len(df) == 0:
        logging.info(f'Query {vsn} {args.start} {args.end} returned 0 records')
        return 0

    out_df = generate_job_records(df)
    output = "jobs.csv"
    out_df.to_csv(output, index=False)
    logging.info(f'Created {output}. Done.')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    cli()

    # exit(main(args))
