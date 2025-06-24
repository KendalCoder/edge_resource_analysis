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