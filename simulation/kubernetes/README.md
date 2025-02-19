# Edge Simulation with Kubernetes
This simulation forms a computing cluster of multiple devices and creates workloads to simulate various scheduling policies for research. Users can create their own scheduler (See [the document](src/scheduler/README.md) for detail).

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

## Using a Simple Cluster
This cluster creates simulated nodes and workloads. 


## Using a Kubernetes Cluster

> WARNING: this is under active development. Things may not work as expected.

To create a cluster,

```bash
./setup.sh
```