# Simantha

Simantha is a package for simulating discrete manufacturing systems. It is designed to model asynchronous production systems with finite buffers.

The package provides classes for the following core manufacturing objects that are used to create a system:
* **Source**: Introduces raw, unprocessed parts to the system.
* **Machine**: Continuously retrieves, processes, and relinquishes parts. May also be subject to periodic degradation, failure, and repair.
* **Buffer**: Stores parts awaiting processing at a machine.
* **Sink**: Collects finished parts that exit the system. 
* **Maintainer**: Repairs degrading machines according to the specified maintenance policy. 

For the complete Simantha documentation, see https://simantha.readthedocs.io/en/latest/.

## Installation

Simantha can be installed via `pip` using:

```
pip install simantha
```

## Quickstart

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
