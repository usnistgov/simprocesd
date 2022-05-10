# Sim-PROCESD

Sim-Procesd is a discrete event simulation package written in Python that is designed to model the behavior of discrete manufacturing systems. Specifically, it focuses on asynchronous production lines with finite buffers. It also provides functionality for modeling the degradation and maintenance of machines in these systems.

In addition to modeling the behavior of existing systems, Sim-PROCESD is also intended to help with optimizing those systems by simulating various changes to them and reviewing the results. For instance, users may be interested in evaluating alternative maintenance policies for a particular system.

The software is available for public use through a publicly available Github repository. Any user may create a fork (copy) of the repository to freely experiment (e.g., class extensions to model complex processes) with the code without affecting the original source code.

**NOTE:** Sim-PROCESD project is in early development and may receive updates that are not backwards compatible.


## Installation
```
pip install sim-procesd
```

## Quickstart

The package provides following objects for modeling a manufacturing process:
- **Source**: Introduces new parts to the system.
- **Machine**: Retrieves, processes, and relinquishes parts. Can be subject to degradation, failures, and repairs.
- **Buffer**: Retrieves, stores, and relinquishes parts.
- **Filter**: Conditionally allow parts to pass between its upstream and downstream.
- **Sink**: Collects finished parts that exit the system.
- **Maintainer**: Performs requested maintenance as soon as possible. Has a configurable capacity.
- **Probes & Sensors**: Take periodic or on-demand readings and record them. The recorded data is accessible during the simulation and after.

#### Examples

A collection of examples is available at [simprocesd/examples](/simprocesd/examples).

- Basic example: [SingleMachine.py](/simprocesd/examples/SingleMachine.py)  
- Parallel processing: [ParallelStations.py](/simprocesd/examples/ParallelStations.py)  
- Utilizing Part quality: [CustomPart.py](/simprocesd/examples/CustomPart.py)  
- Machine with configurable fault rates: [SingleMachineWithFaults.py](/simprocesd/examples/SingleMachineWithFaults.py)   
- Machine with a health tracker: [ConditionBasedMaintenance.py](/simprocesd/examples/ConditionBasedMaintenance.py)  
- Maintenance policy testing: [MaintenanceOptimization.py](/simprocesd/examples/MaintenanceOptimization.py)  

## Simantha
Sim-PROCESD was forked from the Simantha project which can be found [here](https://github.com/m-hoff/simantha).

## Who We Are
This tool is part of the Smart Manufacturing Industrial AI Management & Metrology project in the Smart Connected Systems Division (Communications Technology Laboratory) at NIST.

Contacts:
- [Mehdi Dadfarnia](https://www.nist.gov/people/mehdi-dadfarnia), Maintenance & Development
- [Serghei Drozdov](https://www.nist.gov/people/serghei-drozdov), Lead Developer
- [Michael Sharp](https://www.nist.gov/people/mehdi-dadfarnia), Project Leader
