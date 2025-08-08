# Scheduling Policy
Researchers are welcome to develop, test, and evaluate scheduling algorithms. 


# Edge Computing Task Scheduler Simulation


This repository simulates different task scheduling strategies in an edge computing environment. It supports multiple schedulers, logs system performance, and allows users to visualize metrics like energy consumption and task throughput.


---



## File Overview


| File / Folder         | Purpose |


| `run.py`              | Entry point to start the simulation. Loads config, scheduler, and runs tasks. |


| `mywaggle.yaml`        | Configuration file for nodes and workloads. |




---


#### Kubernetes-Style Task Scheduling Simulation for Edge Devices


This module simulates different scheduling strategies for deploying workloads on a distributed set of edge compute nodes. It mimics a Kubernetes-style environment, enabling experimentation with resource-aware, energy-aware, and optimization-driven task schedulers.


#### Useful for:

• Simulating energy-aware workload distribution.

• Comparing different schedulers like greedy, workload-aware, or EDF.

• Logging and visualizing node performance over time.


⸻


# Directory: simulation/kubernetes/src/scheduler/


Each Python file in this folder implements a different scheduling policy. These schedulers determine how workloads are assigned to virtual nodes based on custom logic such as CPU load, fairness, task deadlines, or energy constraints.






# File Description

### wagglecheduler.py
	
Baseline greedy scheduler: assigns each workload to the first node that can accept it, without optimization. Useful for comparison.

### fairsharescheduler.py

Picks the node with the least CPU usage that can fit the workload. Also has energy logging for each node.


### randomscheduler.py
	
Assigns each workload to a random node, regardless of resource availability. Serves as a naive baseline for performance comparison.

### workloadawarescheduler.py
	
Attempts to schedule based on workload characteristics such as size or type. Helps improve resource matching.

### edfscheduler.py

Implements Earliest Deadline First (EDF) scheduling to prioritize tasks with the closest deadlines. Useful for time-sensitive applications.

### centralized_solver.py (under development)

Uses a centralized optimization solver to compute global optimal task placement. Slower but more accurate in theory.

### dual_node.py (under development)

A dual-descent optimization node module used for refining resource allocation in schedulers like Fairshare.

⸻


#### 🧵 Example: FairshareScheduler

• Selects the least-loaded node by checking CPU usage.

• Performs dual descent to optimize node configuration before scheduling.

• Logs energy consumption based on CPU use (power = cpu × 2.5).

• Compatible with TensorBoard scalar logging for visualization.





#### 🧵 Example: WaggleScheduler

• Greedy-first approach: tries nodes in order and assigns to the first one that can accept the workload.

• No optimization or energy-awareness — serves as a baseline.





# How to Change the Scheduler
- change the scheduler to see different results 

In your config file (mywaggle.yaml), find the line:
```
Scheduler: WaggleScheduler 
```
Or 
```
Scheduler : FairShareScheduler 
```
Then re-run run.py.


