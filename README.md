# SimPROCESD: Simulated-Production Resource for Operations & Conditions Evaluations to Support Decision-making

SimPROCESD is a discrete event simulation package written in Python that is designed to model the behavior of discrete manufacturing systems. Specifically, it focuses on asynchronous production lines with finite buffers. It also provides functionality for modeling the degradation and maintenance of machines in these systems.

In addition to modeling the behavior of existing systems, SimPROCESD is also intended to help with optimizing those systems by simulating various changes to them and reviewing the results. For instance, users may be interested in evaluating alternative maintenance policies for a particular system.

The software is available for public use through a publicly available GitHub repository. Any user may create a fork (copy) of the repository to freely experiment (e.g., class extensions to model complex processes) with the code without affecting the original source code.

**NOTE:** SimPROCESD project is in early development and may receive updates that are not backwards compatible.

## GitHub Pages
Additional documentation, including API, is available at: [https://usnistgov.github.io/simprocesd/](https://usnistgov.github.io/simprocesd/)

## Installation

SimPROCESD can be installed via `pip` using:

```
pip install simprocesd
```

To also include optional dependencies needed to some of the examples:

```
pip install simprocesd[examples]
```


### Installation Requirements
Using SimPROCESD requires:
- Python ≥ 3.7:
- matplotlib ≥ 3.5 for using plot functions and running certain examples.
- [optional] scipy ≥ 1.5.2 and numpy ≥ 1.21 for running certain examples.


## Quickstart

The package provides following objects for modeling a manufacturing process:
- **Source**: Introduces new parts to the system.
- **Machine**: Retrieves, processes, and relinquishes parts. Can be subject to degradation, failures, and repairs.
- **Buffer**: Retrieves, stores, and relinquishes parts.
- **DecisionGate**: Conditionally allow parts to pass between its upstream and downstream.
- **Sink**: Collects finished parts that exit the system.
- **Maintainer**: Performs requested maintenance as soon as possible. Has a configurable capacity.
- **Probes & Sensors**: Take periodic or on-demand readings and record them. The recorded data is accessible during the simulation and after.

#### Examples

A collection of examples is available at [examples](/examples).

- Basic example: [SingleMachine.py](/examples/SingleMachine.py)  
- Parallel processing: [ParallelStations.py](/examples/ParallelStations.py)  
- Utilizing Part quality: [PartQuality.py](/examples/PartQuality.py)  
- Machine with configurable fault rates: [SingleMachineWithFaults.py](/examples/SingleMachineWithFaults.py)   
- Machine with a health tracker: [ConditionBasedMaintenance.py](/examples/ConditionBasedMaintenance.py)  
- Maintenance policy testing: [MaintenanceOptimization.py](/examples/MaintenanceOptimization.py)  

## Simantha
SimPROCESD was forked from the original Simantha project which can be found [here](https://github.com/m-hoff/simantha). Another iteration of [Simantha](https://github.com/usnistgov/simantha) extends a few capabilities and examples to prepare it for the modeling of condition monitoring systems and prognostics and health management tools.

 

## Who We Are
This tool is part of the Smart Manufacturing Industrial AI Management & Metrology project in the Smart Connected Systems Division (Communications Technology Laboratory) at NIST.

Contacts:
- [Mehdi Dadfarnia](https://www.nist.gov/people/mehdi-dadfarnia), Maintenance & Development
- [Serghei Drozdov](https://www.nist.gov/people/serghei-drozdov), Lead Developer
- [Michael Sharp](https://www.nist.gov/people/michael-sharp), Project Leader


## License
SimPROCESD and all of it's associated projects are in the public domain (see License). For more information and to provide feedback, please open an issue, submit a pull-request, or email the point of contact (above).


## Citing this software 
Citation examples can be found at: https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications 

DOI: https://data.nist.gov/od/id/mds2-2733
