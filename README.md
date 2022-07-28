# Sim-PROCESD: Simulated-Production Resource for Operations & Conditions Evaluations to Support Decision-making

Sim-PROCESD is a discrete event simulation package written in Python that is designed to model the behavior of discrete manufacturing systems. Specifically, it focuses on asynchronous production lines with finite buffers. It also provides functionality for modeling the degradation and maintenance of machines in these systems.

In addition to modeling the behavior of existing systems, Sim-PROCESD is also intended to help with optimizing those systems by simulating various changes to them and reviewing the results. For instance, users may be interested in evaluating alternative maintenance policies for a particular system.

The software is available for public use through a publicly available Github repository. Any user may create a fork (copy) of the repository to freely experiment (e.g., class extensions to model complex processes) with the code without affecting the original source code.

**NOTE:** Sim-PROCESD project is in early development and may receive updates that are not backwards compatible.


## Installation

Simantha can be installed via `pip` using:

```
pip install sim-procesd
```

### Installation Requirements
Using Simantha requires Python ≥ 3.6 and, optionally, SciPy ≥ 1.5.2 for running the included tests. 


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
Sim-PROCESD was forked from the original Simantha project which can be found [here](https://github.com/m-hoff/simantha). Another iteration of [Simantha](https://github.com/usnistgov/simantha) extends a few capabilities and examples to prepare it for the modeling of condition monitoring systems and prognostics and health management tools.

 

## Who We Are
This tool is part of the Smart Manufacturing Industrial AI Management & Metrology project in the Smart Connected Systems Division (Communications Technology Laboratory) at NIST.

Contacts:
- [Mehdi Dadfarnia](https://www.nist.gov/people/mehdi-dadfarnia), Maintenance & Development
- [Serghei Drozdov](https://www.nist.gov/people/serghei-drozdov), Lead Developer
- [Michael Sharp](https://www.nist.gov/people/michael-sharp), Project Leader


## Citing this software 
Citation examples can be found at: https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications 

DOI: tbd
