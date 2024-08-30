# Simulations
This lists simulations to run against our datasets.

## COSCO
The COSCO framework supports simulations using cuscom schedulers and datasets. To run a Docker container of the framework on a Linux machine,

```bash
cosco/run_cosco_docker.sh
```

The output would be similar to,
```bash
Removing existing COSCO container...
cosco
Done.
Using the current directory as data folder inside the container.
Current directory: /home/theone/repo/edge_resource_analysis/scripts
Running a Docker container for COSCO...
9936f2c4e5c92209143518171e66c160497e74ef3826aab488a2410e13eb18c7
Done.
```

Then, you can use `docker exec` or GUI tools such as Visual Studio Code to get into the container for development. The container mounts `/data` folder from the host machine. You can use the folder to save some data permanently, after the container terminates.