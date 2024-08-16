#!/usr/bin/python3

import logging
import argparse

from utils import *


def main(args):
    vsn = args.vsn.upper()
    output = "jobs.csv"
    start = f'-{args.start}'
    if args.end != "":
        end = f'-{args.end}'
    else:
        end = ""
    logging.info(f'Querying job data for node {vsn} from {start} to {end}')
    
    df = fill_completion_failure(parse_events(get_data(vsn, start, end)))
    df["timestamp"] = df["timestamp"].map(lambda x: x.isoformat())
    df["completed_at"] = df["completed_at"].map(lambda x: x.isoformat())
    df["failed_at"] = df["failed_at"].map(lambda x: x.isoformat())
    df = df.sort_values(by="plugin_name")
    df.to_csv(output, index=False)
    logging.info(f'Created {output}')
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", dest="debug",
        action="store_true",
        help="Enable debugging")
    parser.add_argument(
        "-v", "--vsn", dest="vsn",
        action="store", type=str,
        help="VSN")
    parser.add_argument(
        "-s", "--start", dest="start",
        action="store", required=True,
        help="Start time of the query, e.g. 1h, 10d")
    parser.add_argument(
        "-e", "--end", dest="end",
        action="store", default="",
        help="End time of the query, e.g. 1h, 10d")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    exit(main(args))
