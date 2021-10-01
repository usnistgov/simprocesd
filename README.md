# Simantha

Simantha is a package for simulating discrete manufacturing systems. It is designed to model asynchronous production systems with finite buffers.

The package provides classes for the following core manufacturing objects that are used to create a system:
* **Source**: Introduces raw, unprocessed parts to the system.
* **Machine**: Continuously retrieves, processes, and relinquishes parts. May also be subject to periodic degradation, failure, and repair.
* **Buffer**: Stores parts awaiting processing at a machine.
* **Sink**: Collects finished parts that exit the system. 
* **Maintainer**: Repairs degrading machines according to the specified maintenance policy. 

## Purpose

Simantha is a discrete-event simulation package written in Python that is designed to model the behavior of discrete manufacturing systems. Specifically, it focuses on asynchronous production lines with finite buffers. It also provides functionality for modeling the degradation and maintenance of machines in these systems. Classes for five basic manufacturing objects are included: source, machine, buffer, sink, and maintainer. These objects can be defined by the user and configured in different ways to model various real-world manufacturing systems. The object classes are also designed to be extensible so that they can be used to model more complex processes. 

In addition to modeling the behavior of existing systems, Simantha is also intended for use with simulation-based optimization and planning applications. For instance, users may be interested in evaluating alternative maintenance policies for a particular system. Estimating the expected system performance under each candidate policy will require a large number of simulation replications when the system is subject to a high degree of stochasticity. Simantha therefore supports parallel simulation replications to make this procedure more efficient. 

The software is available for public use through a publicly available Github repository. Any user with a Github account may create a fork (copy) of the repository to freely experiment (e.g., object class extensions to model complex processes) with the code without affecting the original source code.


## Quick Links
For the complete Simantha documentation, see https://simantha.readthedocs.io/en/latest/ . Here, you will find:
- Reference for all the objects in Simantha
- Examples of discrete manufacturing system models
- Use cases that extend Simantha for such things as condition-based maintenance


Simantha and all of it's associated projects are in the public domain (see License). For more information and to provide feedback, please open an issue, submit a pull-request, or email the point of contact (below).


## Installation

Simantha can be installed via `pip` using:

```
pip install simantha
```

### Installation Requirements
Using Simantha requires Python ≥ 3.6 and, optionally, SciPy ≥ 1.5.2 for running the included tests. 


### Quickstart

The following is an example of the creation and simulation of a simple two-machine one-buffer line.

<p align="center">
  <img src=docs/images/two_machine_one_buffer.png>
</p>

```python
from simantha import Source, Machine, Buffer, Sink, System

# Create objects
source = Source()
M1 = Machine(name='M1', cycle_time=1)
B1 = Buffer(name='B1', capacity=5)
M2 = Machine(name='M2', cycle_time=1)
sink = Sink()

# Specify routing
source.define_routing(downstream=[M1])
M1.define_routing(upstream=[source], downstream=[B1])
B1.define_routing(upstream=[M1], downstream=[M2])
M2.define_routing(upstream=[B1], downstream=[sink])
sink.define_routing(upstream=[M2])

# Create system
system = System(objects=[source, M1, B1, M2, sink])

# Simulate
system.simulate(simulation_time=100)

# Output:
# Simulation finished in 0.00s
# Parts produced: 99
```

For additional examples, see [simantha/examples](/simantha/examples).


## Who We Are
This tool is part of the Smart Manufacturing Operations Management (SMOM) project in the Smart Connected Systems Division (Communications Tech Laboratory) at NIST.
Simantha has been developed by Michael Hoffman as a software package for the Python 3 programming language, and is being maintained and extended by Mehdi Dadfarnia:

- [Mehdi Dadfarnia](https://www.nist.gov/people/mehdi-dadfarnia), Maintenance & Development
