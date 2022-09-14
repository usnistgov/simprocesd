# Code Introduction

Some of the basic that will help understand how SimPROCESD works and how to use it.

## Objects

The package provides the following objects for modeling a manufacturing process:
- **Source**: Introduces new parts to the system.
- **Machine**: Retrieves, processes, and relinquishes parts. Has a status tracker.
 - **MachineStatusTracker**: Tracks machine's condition, triggers hard failures, and contains maintenance information.
- **Buffer**: Retrieves, stores, and relinquishes parts.
- **DecisionGate**: Conditionally allow parts to pass between its upstream and downstream.
- **Sink**: Collects finished parts that exit the system.
- **Maintainer**: Performs requested maintenance as soon as possible. Has a configurable capacity.
- **Probes & Sensors**: Take periodic or on-demand readings and record them. The recorded data is accessible during the simulation and after.

## Upstream/s

When deviceA can receive parts from deviceB then deviceA is known as the upstream of deviceB.  
SImilarly, deviceB is a downstream of deviceA.
The links between different devices are configured by setting the `upstream` parameter.  
```
    S1 = Source()
    S2 = Source()
    M1 = Machine(upstream = [S1, S2])
```
- In this setup, `M1` can receive parts from both `S1` and `S2`.  
- Default `Machine` can accept only 1 part at a time from an upstream.

The upstream property can also be replaced with a new list after an object is created.
```
M1 = Machine(upstream = [S1, S2])
M1.set_upstream([S1])  # S2 is no longer upstream of M1.
```

A device's upstream list can not contain the device itself. A circular flow is possible if deviceA 
is set as upstream of deviceB and deviceB is set as upstream of deviceA.

### Multiple Downstreams

Configuring a device to pass parts to multiple devices:
```
    S1 = Source()
    M1 = Machine(upstream = [S1])
    B1 = Buffer(upstream = [S1], capacity = 5)
```
- In this setup, parts from `S1` can go to either `M1` or `B1`.  
- As parts become available in any device they will be passed to one of their downstreams prioritizing
downstreams that has been waiting for a part the longest.

## Simple Example

```
    system = System()
    part = Part()
    source = Source(sample_part = part, cycle_time = 1)
    M1 = Machine(upstream = [source], cycle_time = 1)
    sink = Sink(upstream = [M1])
    system.simulate(simulation_duration = 100)
```
Part's flow through the devices: `source` -> `M1` -> `sink`

Same example with additional comments:
```
    # System needs to be created first so that other simulation objects
    # can register themselves with it automatically.
    system = System()

    # Create a part object to be used as a sample in the Source.
    part = Part()

    # Source will create copies of the sample part every 1 time unit
    source = Source(sample_part = part, cycle_time = 1)

    # Create Machine that gets parts from Source and takes 1 time unit
    # to process the part before passing it downstream.
    M1 = Machine(upstream = [source], cycle_time = 1)

    # Sink is the end of the line and can only receive parts.
    sink = Sink(upstream = [M1])

    # Run the simulation for 100 time units.
    system.simulate(simulation_duration = 100)
```
* Time units are not specified but will work as long as they are used consistently. For example,
time units can represent seconds as long as that is consistently used throughout the simulation.

## Post-Simulation Analysis

How to go about collecting data during the simulation and retrieving it afterwards.

### Simulated Sensors

Sensor example: [ConditionBasedMaintenance.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ConditionBasedMaintenance.py)

### Integrated Data Collection

SimPROCESD by default records some data about the simulation.
|Description |list_label |sub_label |data_point |
|---|---|---|---|
|Device receives a part |'received_parts' |device_name |(time, part_quality) |
|Device processes a part |'produced_parts' |device_name |(time, part_quality) |
|Work order enteres queue |'enter_queue' |maintainer_name |(time, device_to_maintain, maintenance_tag) |
|Work order begins |'begin_maintenance' |maintainer_name |(time, device_to_maintain, maintenance_tag) |
|Work order completes |'finish_maintenance' |maintainer_name |(time, device_to_maintain, maintenance_tag) |
|Sink receives a part |'collected_part' |sink_name |(time, part_quality, part_value) |
|Source passes a part |'supplied_new_part' |source_name |(time,) |

Example of retrieving a table of raw data for a specific device.
```
    system.simulation_data['produced_parts']['M1']
    # <System>.simulation_data[list_label][sub_label]
    # or
    # <Environment>.simulation_data[list_label][sub_label]
```

That data gets stored in simulation data which is a dictionary with the following structure:

- Key: `list_label` (string)
- Value: Dictionary
    - Key: `sub_label` (string)
    - Value: List of tuples stored with that `list_label` and `sub_label`
        - The list contains data in the order that it was recorded.
        - tuples are `tuple_of_data` from the example below.

Adding new datapoints to be recorded with simulated data is easy:
```
    # During the simulation you can all the following code on any Asset (Device, Machine, Source, etc).
    M1.env.add_datapoint('new label', M1.name, (M1.env.now, self._output.quality))
    # <Asset>.env.add_datapoint(list_label, sub_label, tuple_of_data)
```

These calls can be integrated into other parts like Machine's callbacks:
```
    M1 = Machine(upstream = [source], cycle_time = 1)

    def on_received_part(part):
        M1.env.add_datapoint('received_part_value', M1.name, (M1.env.now, part.value))

    # Configure on_received_part to be called everytime M1 receives a part.
    M1.add_receive_part_callback(on_received_part)
	
    ...run simulation...

    # Print list of recorded tuples
    print(system.simulation_data['received_part_value'][M1.name])
```

### simulation_data Reference

There are build in functions under 
GitHub: [simulation_info_utils.py](https://github.com/usnistgov/simprocesd/blob/master/simprocesd/utils/simulation_info_utils.py) 
that show graphs based on simulation_data.

## Discrete Event Simulator

SimPROCESD is a discrete event simulator which means that the simulation is driven forward by
events. Initial events are created during initialization of the simulated objects and additional
events are generated in process of executing the previous events.

&nbsp;  
Multiple events can be schedules to happen at the exact same time in which case they are
executed in order of [`EventType` priority](https://github.com/usnistgov/simprocesd/blob/master/simprocesd/model/simulation.py#L11) 
(represented by a number).  

&nbsp;  
Example of how `Source` can schedule an event for generating a new part after `cycle_time` has passed:
```
    self.env.schedule_event(                # Environment.schedule_event(...
        self.env.now + self.cycle_time,     # Absolute simulation time when the event will execute.
        self.id,                            # ID of the object whose action the event represents.
        self._prepare_next_part,            # The action to be executed (a function).
        EventType.FINISH_PROCESSING,        # Event type. Helps determine correct execution order.
        '{self.name} prepares part.'        # A debug string to associate with the event.
    )
```
