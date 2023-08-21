# Examples

All of the examples are part of the open source repository on GitHub: [examples/](https://github.com/usnistgov/simprocesd/tree/master/examples)  

Once you have the source code downloaded and the SimPROCESD package installed you can run examples like so:
```
# Navigate to the root folder of SimPROCESD source code and run the following command:
python examples/SingleProcessor.py
```
  
List of examples with notes on what each one shows:

**[SingleProcessor.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SingleProcessor.py)**  
- Basic setup: Source -> PartProcessor -> Sink
 
**[BufferExample.py](https://github.com/usnistgov/simprocesd/blob/master/examples/BufferExample.py)**  
- Using a Buffer.

**[ParallelStations.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ParallelStations.py)**  
- Modeling a multi-stage production line with multiple processors in each stage.
 
**[PartQuality.py](https://github.com/usnistgov/simprocesd/blob/master/examples/PartQuality.py)**  
- Configuring PartProcessors to change part quality of processed parts.
- Using `random.seed(n)` to ensure same results every time the simulation is ran.

**[FilterParts.py](https://github.com/usnistgov/simprocesd/blob/master/examples/FilterParts.py)**  
- Using DecisionGates to manage where parts go based on part quality.

**[VariousFlows.py](https://github.com/usnistgov/simprocesd/blob/master/examples/VariousFlows.py)**  
- Modeling a system with 2 parallel production paths that both share one of the processors.
- Visual representation of the setup (see below):
	- Top diagram: the design being modeled with M3 machine as part of 2 production paths.
	- Bottom diagram: the actual model layout with a single M3 machine followed by 2 filters (DecisionGates) that control part flow.  
	 
```{image} _images/various_flows_diagram.jpg
:alt: various_flows_diagram.jpg
:width: 500px
```

**[ExtendingPartObject.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ExtendingPartObject.py)**  
- Extending Part and PartGenerator classes in order to add a new weight property.
- Using the new classes.

**[OperatingSchedule.py](https://github.com/usnistgov/simprocesd/blob/master/examples/OperatingSchedule.py)**  
- Using ActionScheduler to control when a machine can produce parts.

**[BatchProcessing.py](https://github.com/usnistgov/simprocesd/blob/master/examples/BatchProcessing.py)**  
- Generating and processing of part Batches.
- Using PartBatcher to batch and un-batch parts.

**[SharedResources.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SharedResources.py)**  
- Configuring pools of limited resources.
- Setting up PartProcessors that have to reserve limited resources in order to process parts.

**[ReentrantFlow.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ReentrantFlow.py)**  
- Using Group class to have the same PartProcessor in 2 different stages of production.

**[SingleMachineWithFaults.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SingleMachineWithFaults.py)**  
- Using an extended PartProcessor (MachineWithFaults) class to model periodic faults.
- Configuring fault rate and maintenance times to be based on a geometric distribution.
- Requesting maintenance when the custom machine has a fault.

**[ConditionBasedMaintenance.py](https://github.com/usnistgov/simprocesd/blob/master/examples/ConditionBasedMaintenance.py)**  
- Using an extended PartProcessor (MachineWithDamage) class to model accumulating wear and tear on a device.
- Using sensors to periodically measure accumulated damage and to request maintenance if damage is over threshold.

**[SimulateMultipleTimes.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SimulateMultipleTimes.py)**  
- Running multiple simulations of the model using multiple CPU cores.
- Using `random.seed(n)` to ensure same results every time the simulation is ran.
 
**[MaintenanceOptimization.py](https://github.com/usnistgov/simprocesd/blob/master/examples/MaintenanceOptimization.py)**  
- Setup: 5 parallel processors that accrue damage which negatively impacts part quality.
- Simulating the model with different damage thresholds needed to trigger maintenance.
- Running multiple simulations of each configuration using multiple CPU cores.
- Showing summary graphs of the simulation data.

**[DataExploration.py](https://github.com/usnistgov/simprocesd/blob/master/examples/DataExploration.py)**  
- Setup:
 - 5 parallel processors that accumulate damage over time at different rates.
 - Quality of parts is reduced based on processor's accrued damage since last maintenance.
 - Processors are maintained only when they experience a hard failure.
- Using a sensor to periodically measure Buffer level (how many parts the Buffer has).
- Using built-in graphing functions to show data:
 - Cumulative average throughput over time.
 - Machine damage over time.
 - Cumulative costs/values associated with sourcing parts and final part products.
 - Buffer level over time.

**[SaveSimulationToFile.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SaveSimulationToFile.py)**  
- Saving the System object to a file and loading it back from the file. System stores the current
of the model and all of the recorded datapoints.

**[PaperMillCmsEvaluation.py](https://github.com/usnistgov/simprocesd/blob/master/examples/PaperMillCmsEvaluation.py)[Experiemental]**  
- Simulating a manufacturing system with and without a Condition Monitoring System (CMS).
- Simulating CMS that tracks processor status through a sensor of part quality; the CMS has a
configurable false alert and missed alert rates.
- Track spending and earning with the value property.

**[SharedResourcesComplex.py](https://github.com/usnistgov/simprocesd/blob/master/examples/SharedResourcesComplex.py)[Experiemental]**  
- Using ActionSchedulers, limited shared resources, and a Group in one model.
- Configuring a limited resource whose quantity varies with time.
- Setup:
 - 2 parallel production paths that share one processor.
 - PartProcessors are each set to one of 3 schedules: morning, evening, both.

**[MachineFaultDetection.py](https://github.com/usnistgov/simprocesd/blob/master/examples/MachineFaultDetection.py)[Experiemental]**  
- Determining faulty machine by inspecting final part quality and part routing history.