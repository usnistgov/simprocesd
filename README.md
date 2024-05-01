# SimPROCESD: Simulated-Production Resource for Operations & Conditions Evaluations to Support Decision-making

SimPROCESD is a discrete event simulation package written in Python that is designed to model the behavior of discrete manufacturing systems. Specifically, it focuses on asynchronous production lines with finite buffers. It also provides functionality for modeling the degradation and maintenance of machines in these systems.

In addition to modeling the behavior of existing systems, SimPROCESD is also intended to help with optimizing those systems by simulating various changes to them and reviewing the results. For instance, users may be interested in evaluating alternative maintenance policies for a particular system.

The software is available for public use through a publicly available GitHub repository. Any user may create a fork (copy) of the repository to freely experiment (e.g., class extensions to model complex processes) with the code without affecting the original source code.

**NOTE:** SimPROCESD project is in early development and may receive updates that are not backwards compatible.

## Online Documentation

Additional documentation, including API, is available at: [usnistgov.github.io/simprocesd](https://usnistgov.github.io/simprocesd/)

## Installation

Installing SimPROCESD using **pip**:

```
pip install simprocesd
```

Install SimPROCESD with additional dependencies required by some of the [examples](/examples):

```
pip install simprocesd[examples]
```


### Installation Requirements
Using SimPROCESD requires Python3, version ≥ 3.7

Dependencies (will be automatically installed by pip):
- numpy ≥ 1.21
- matplotlib ≥ 3.5
- dill
- scipy ≥ 1.5.2 (only installed with simprocesd[examples])

#### Examples

A collection of examples can be found in the [examples folder](/examples).

Notes on each example are available at [usnistgov.github.io/simprocesd/examples](https://usnistgov.github.io/simprocesd/examples.html)


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
