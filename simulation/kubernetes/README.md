# Edge Simulation with Kubernetes
This simulation forms a computing cluster of multiple devices and creates workloads to simulate various scheduling policies for research. Users can create their own scheduler (See [the document](src/scheduler/README.md) for detail).

## Install Dependencies
 `pip3 install -r requirements.txt`

## Quick Start
To start a simulation, simply run,

```bash
# Uses mywaggle configuration to set up the simulation
python3 run.py --config mywaggle.yaml
```

After the simulation is finished (or during the simulation), open Tensorboard to see the result,

```bash
tensorboard --logdir logs/
```
- You should see the link after running this command 
- Open the link and see the graphs and plots

These are useful links about Tensorboard:
https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.tensorflow.org/tensorboard/get_started&ved=2ahUKEwi2k6HGsYqOAxUPPjQIHZMlI6sQFnoECBIQAQ&usg=AOvVaw2zoEfsLy_AcckWcLnf6tdT

https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.datacamp.com/tutorial/tensorboard-tutorial&ved=2ahUKEwinkMXUsYqOAxWEOTQIHbXsBewQFnoECEIQAQ&usg=AOvVaw2SiaeB3BS3Eb2vzAyU_HLc


## Using a Simple Cluster
This cluster creates simulated nodes and workloads. 


## Using a Kubernetes Cluster

> WARNING: this is under active development. Things may not work as expected.

To create a cluster,

```bash
./setup.sh
```

## How to Run a Simulation


```bash

python3 run.py --config mywaggle.yaml


To see plots on tensorboard 
```bash
tensorboard --logdir logs/
```


TensorBoard will start a local web server. You’ll see output like:

```
TensorBoard 2.13 at http://localhost:6006/ (Press CTRL+C to quit)

```
Open your browser and go to:
```
http://localhost:6006
```
#TODO descibe how to interpret results in tensorboard 



##  File Overview (Visualization)
 Description : 

| `scripts/CSVexport.py`            | Handles saving of performance and energy metrics.|
#TODO : Be more specific in what csv export does

| `src/scripts/visualization.py`|

#TODO description



| `/logs/`               | Stores run logs including per-task and per-node metrics. |


| `/notebooks/`          | Jupyter notebooks for post-simulation analysis and plotting. |



# Requirements for Visualization 


Make sure the following packages are installed:

```
pip install pandas matplotlib seaborn
```

## How to retrieve log to use for visualization 
#### (Check which scheduler you ran from mywaggle.yaml )

-Go to logs and find the latest run or the run based on the date your looking for and change {DefaultScheduler} to the scheduler you ran . 


## How to Generate Plots from Logs

Scheduler Log Analysis & Visualization


This section explains the purpose and usage of the two Python scripts (CSVexport.py & visualization.py) used to extract, process, and visualize metrics from scheduler logs in the edge computing simulation project.


⸻


1. CSVexport .py


Purpose:

This script converts scalar logs from TensorBoard .tfevents files into a readable CSV format. It enables easier analysis of metrics like energy usage, task duration, or CPU load logged during the simulation.


What It Does:

• Loads scalar values from TensorBoard logs.

• Outputs a CSV file with columns: step, tag, and value.

• Includes a helper to pick the latest log directory automatically.

• Can also simulate logs using SummaryWriter (for testing visualizations).


How to Use:

1. Make sure your TensorBoard event logs is in the logs folder.

2. Set the log_dir_event_file path with the path of your event log in the script. By copying the directory name . 
Ex:  log_dir_event_file = "kubernetes/logs/20250723-111951-FairShareScheduler"  # Path to the TensorBoard event file 

- change line 53 and 55 in CSV export based on which scheduler your running 
Ex:  output_csv = "FairShareScheduler_task_log.csv"


3. Run the script:
 
 - Change the directory by using cd src/scripts

 Go to CSVexport file 
Run & Debug on left side panel in VScode or whatever code runner for your IDE 

or 

Bash
```
python3 CSVexport.py 
```

Output: a CSV file like FairShareScheduler_task_log.csv.


⸻


2. Visualization .py


Purpose:

This script analyzes one or more scheduler logs and compares key metrics such as task counts, energy usage, task durations, and efficiency across different schedulers.


Main Features:

• Parses and preprocesses CSV logs.

• Computes per-node metrics like:

• Total and mean energy consumption

• Task duration statistics

• Task efficiency (tasks per unit time)

• Optional: CPU and memory stats (if present in logs)

• Aggregates and compares results across schedulers.

• Generates bar charts and summary CSVs.


How to Use:

1. Ensure you have one or more log CSVs from tensorboard_to_csv.py.

2. Define your list of scheduler names (e.g., ["WaggleScheduler", "FairScheduler"]).


Go to 
vis-interactive.ipynb

 Or 

Bash 

python3 visualization.py




# Outputs:


## Where Logs Are Saved


Simulation logs are saved to the /logs/ directory. You’ll find:
```
• {scheduler name} tasks.csv: logs for all tasks (start time, end time, node used, energy consumed, etc.)
```


• scheduler_comparison_metrics.csv: a summary table

• .png plots for each metric in the plots/ directory

• Console table summarizing each scheduler



Example Output Plots:

• total_energy_per_scheduler.png

• avg_task_time_per_scheduler.png

• task_efficiency_per_scheduler.png

