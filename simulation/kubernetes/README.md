# Edge Simulation with Kubernetes
This simulation forms a computing cluster of multiple devices and creates workloads to simulate various scheduling policies for research. Users can create their own scheduler (See [the document](src/scheduler/README.md) for detail).

## Install Dependencies
 `pip3 install -r requirements.txt`


## Using a Simple Cluster
This cluster creates simulated nodes and workloads. 


## Using a Kubernetes Cluster

> WARNING: this is under active development. Things may not work as expected.

To create a cluster,

```bash
./setup.sh
```

## Quick Start


To start a simulation, simply run,

```bash
# Uses mywaggle configuration to set up the simulation
python3 run.py --config mywaggle.yaml
```

#### After the simulation is finished (or during the simulation), open Tensorboard to see the result

```bash
tensorboard --logdir logs/
```
- You should see the link after running this command 
- Open the link and see the graphs and plots




TensorBoard will start a local web server. You’ll see output like:

```
TensorBoard 2.13 at http://localhost:6006/ (Press CTRL+C to quit)

```
Open your browser and go to:
```
http://localhost:6006
```

These are useful links about Tensorboard:
https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.tensorflow.org/tensorboard/get_started&ved=2ahUKEwi2k6HGsYqOAxUPPjQIHZMlI6sQFnoECBIQAQ&usg=AOvVaw2zoEfsLy_AcckWcLnf6tdT

https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.datacamp.com/tutorial/tensorboard-tutorial&ved=2ahUKEwinkMXUsYqOAxWEOTQIHbXsBewQFnoECEIQAQ&usg=AOvVaw2SiaeB3BS3Eb2vzAyU_HLc

## Interpreting Results in TensorBoard

After launching TensorBoard with `tensorboard --logdir logs/`, open the provided link in your browser (usually http://localhost:6006). You will see a dashboard with several tabs and plots.

### Key Steps

1. **Select the Run(s):**
    - On the left panel, choose the experiment(s) you want to view. Each run ( different schedulers or configurations) appears as a separate entry.

2. **Focus on Relevant Metrics:**
    - Common metrics logged include:
      - **Energy Usage:** Tracks total or per-node energy consumption over time.
      - **Task Duration:** Shows how long tasks take to complete.
      - **CPU/Resource Utilization:** Indicates how efficiently resources are used.
      - **Task Efficiency:** Tasks completed per unit time.
    - Use the "Scalars" tab to view these metrics as line plots.


Ex : node_t001-nxcore_cpu
node_t002-nxcore_finished_workloads


3. **Compare Runs or Configurations:**
    - Overlay multiple runs to compare different schedulers or parameter settings.
    - Use the checkboxes to toggle visibility of each run.
    - Look for trends, such as lower energy usage or shorter task durations, to identify better-performing schedulers.

4. **Tips and Caveats:**
    - Hover over plots to see exact values at each step.
    - Use smoothing to reduce noise in plots, but be careful not to over-smooth and hide important details.
    - If metrics are missing, ensure your simulation and logging scripts are configured correctly.
    - For large logs, TensorBoard may take time to load all data.

### Example: Comparing Schedulers

- If you ran simulations with both `Waggle Scheduler` and `FairShareScheduler`, select both runs and compare their energy usage and task duration plots.
- A scheduler with lower energy usage and shorter task durations is generally more efficient.

For more details, refer to the [TensorBoard Getting Started Guide](https://www.tensorflow.org/tensorboard/get_started). 



##  File Overview (Visualization)
 Description : 

| `scripts/CSVexport.py`            | Handles saving of performance and energy metrics.Extracts scalar metrics (such as energy usage, task duration, CPU load, etc.) from TensorBoard `.tfevents` logs and converts them into a structured CSV file. The CSV includes columns for step, metric tag, and value, making it easier to analyze and visualize simulation results outside of TensorBoard. The script can automatically select the latest log directory and supports exporting logs for different schedulers by adjusting configuration lines. |

| `src/scripts/visualization.py`  | Analyzes and visualizes metrics from exported CSV logs. It loads one or more scheduler CSV files, computes statistics such as total and average energy consumption, task durations, and efficiency, and generates comparative plots, bar charts, and summary tables. The script helps compare scheduler performance and outputs results as PNG images and summary CSV files for further analysis. |



| `/logs/`               | Stores run logs including per-task and per-node metrics. |


| `/notebooks/`          | Jupyter notebooks for post-simulation analysis and plotting. |



# Requirements for Visualization 


Make sure the following packages are installed:

```
pip install pandas matplotlib seaborn
```

## How to retrieve log to use for visualization 
#### (Check which scheduler you ran from mywaggle.yaml )

- Go to logs and find the latest run or the run based on the date your looking for and change {DefaultScheduler} to the scheduler you ran . 


## How to Generate Plots from Logs

### Scheduler Log Analysis & Visualization


- This section explains the purpose and usage of the two Python scripts (CSVexport.py & visualization.py) used to extract, process, and visualize metrics from scheduler logs in the edge computing simulation project.




## 1. CSVexport .py


Purpose:

This script converts scalar logs from TensorBoard .tfevents files into a readable CSV format. It enables easier analysis of metrics like energy usage, task duration, or CPU load logged during the simulation.


What It Does:

• Loads scalar values from TensorBoard logs.

• Outputs a CSV file with columns: step, tag, and value.

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

#### Bash
```
python3 CSVexport.py 
```

Output: a CSV file like FairShareScheduler_task_log.csv.




## 2. Visualization .py


> warning : under development 

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

1. Ensure you have one or more log CSVs from CSVexport.py.

2. Define your schedulers name in ipynb for the filename ["WaggleScheduler", "FairScheduler"] or in visualization.py .


#### Go to 
```
vis-interactive.ipynb
```
 Or 

#### Bash 
```
python3 visualization.py
```



## Outputs:


### Where Logs Are Saved


Simulation logs are saved

You’ll find in this directory :

```
• {scheduler name} tasks.csv: logs for all tasks (start time, end time, node used, energy consumed, etc.)
```


• .png plots for each metric in the plots/ directory

• Console table summarizing each scheduler



### Example Output Plots:
```
•total_energy_per_scheduler.png

•avg_task_time_per_scheduler.png

•task_efficiency_per_scheduler.png
```

