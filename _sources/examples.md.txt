# Examples

All of the examples are part of the open source repo on GitHub: [examples/](https://github.com/usnistgov/simprocesd/tree/master/examples)  

Once you have simprocesd package installed and the source code repository downloaded you can run examples like so:
```
python simprocesd_code_repo/examples/SingleMachine.py
```

**[SingleMachine.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SingleMachine.py)**  
- Examples of a basic setup where:
 - a source creates parts
 - then a machine processes the parts
 - and then the parts are collected by the sink
- Source and sink are required and are used in the rest of examples as well.

**[ConditionBasedMaintenance.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ConditionBasedMaintenance.py)**  
- Setup machines that accumulate damage over time.
- Setup sensors to periodically measure machine damage and request maintenance if sufficient damage is present.
- Configure a dynamic maintenance time that depends on the current machine damage.
 
**[PartQuality.py](https://github.com/usnistgov/simprocesd/blob/master/examples/PartQuality.py)**  
- Setup machines that change part quality as they get processed.

**[DataExploration.py](https://github.com/usnistgov/simprocesd/blob/master/examples/DataExploration.py)**  
- Setup a Buffer with a sensor measuring buffer level (how many parts it is holding).
- Setup parallel machines that accumulate damage over time at different rates.
- Quality of parts is reduced based on machine's accrued damage since last maintenance.
- Machines are maintained only when they experience a hard failure.
- Demonstrate using built-in graph functions and plotting sensor data.
 - Cumulative average throughput over time.
 - Machine damage over time.
 - Cumulative costs/values associated with sourcing parts and final part products.
 - Buffer level over time.

**[ExtendingPartObject.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ExtendingPartObject.py)**  
- Extend part object to have a new property.
- Setup machines that modify new property.

**[FilterParts.py](https://github.com/usnistgov/simprocesd/blob/master/examples/FilterParts.py)**  
- Setup `DecisionGate` objects to manage where parts should go based on their state.
 
**[MaintenanceOptimization.py](https://github.com/usnistgov/simprocesd/blob/master/examples/MaintenanceOptimization.py)**  
- Setup 5 parallel machines that accrue damage which negatively impacts part quality.
- Run a series of simulations where a different damage threshold is used to trigger machine maintenance.
- Show final results in graphs to assist with deciding the best maintenance policy.

**[ParallelStations.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ParallelStations.py)**  
- Setup a multi-stage configuration with multiple machines in each stage running in parallel.

**[SingleMachineWithFaults.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SingleMachineWithFaults.py)**  
- Setup a machine with periodic faults and maintenance times determined by geometric distributions.
- Request maintenance when machine fails.
 
**[BufferExample.py](https://github.com/usnistgov/simprocesd/blob/master/examples/BufferExample.py)**  
- Setup two machines with a buffer in between.

**[TwoMachinesWithFaults.py](https://github.com/usnistgov/simprocesd/blob/master/examples/TwoMachinesWithFaults.py)**  
- Setup two machiens with periodic faults.
- Configure maintainer to repair the faults when they occur.

**[VariousFlows.py](https://github.com/usnistgov/simprocesd/blob/master/examples/VariousFlows.py)**  
- Setup a configuration where the same machine is used in multiple steps of the processing.
- [Visual representation of the setup.](https://github.com/usnistgov/simprocesd/blob/master/examples/various_flows_diagram.jpg)

**[PaperMillCmsEvaluation.py](https://github.com/usnistgov/simprocesd/blob/master/examples/PaperMillCmsEvaluation.py)[Experiemental]**  
- Simulate a manufacturing system with and without Condition Monitoring System (CMS) to get expected benefit 
of using a CMS.
- Setup a simulated CMS that tracks machine status through a sensor of part quality and has configurable 
false alert and missed alert rates.
- Setup machines with periodic soft faults, cost of maintenance, and cost of false alerts.
