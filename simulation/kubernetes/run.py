import argparse
import logging
import yaml

from src.runner import Runner


def main(args):
    logging.info("Simulation is started.")
    logging.info("Loading the configuration...")
    with open(args.config, "r") as file:
        config = yaml.safe_load(file)

    with Runner(config=config, logger=logging) as r:
        r.run()
    
    logging.info("Simulation is finished.")
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", dest="config",
        action="store",
        help="Configuration file in yaml")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s - %(filename)s:%(lineno)d: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    exit(main(args))