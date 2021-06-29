System Model
============

The follow sections describe the underlying manufacturing system model that is used by Simantha.


Event Execution Priority
------------------------

Simantha follows the slotted time discrete event system setting for handling simulation events. The slotted time case indicates that all system state transitions occur at discrete time intervals as opposed to transitions occurring in continuous time. The following describes the state changing convention for machines and buffers under the slotted time case [1]_:

    *Machine state* ... is determined *at the beginning of each time slot*. This implies that a chance experiment, carried out at the beginning of each time slot, determines whether the machine is up or down during this time slot.

    *Buffer state* is determined *at the end of each time slot*. This implies that buffer occupancy may change only at the end of a time slot. For instance, if the state of the buffer was 0 at the end of the previous time slot, then the downstream machine does not produce a part during the subsequent time slot, even if it is up. If the buffer state was :math:`h \neq 0` and the downstream machine was up and not blocked, then the state of the buffer at the end of the next time slot is :math:`h` if the upstream machine produces a part, or :math:`h-1` if the upstream machine fails to produce.

Simultaneous simulation events are therefore categorized into two classes: events at the end of a time slot and events at the beginning of the next time slot. Consider, for example, a single machine that is scheduled to place a finished part downstream and undergo failure at the same simulation time. According to our state change convention, this machine would first place the part downstream (since buffer state changes occur at the end of a time slot) and then fail (since machine state changes occur at the beginning of a time slot). If the order of these events was reversed, the machine would first fail, causing it to discard its current part and cancel the yet to be executed event of placing that part downstream. Thus a specified order of these events is needed for consistent simulation output. 

The following events are listed in order of highest priority (executed earlier) to lowest priority (executed later) as they are implemented in Simantha:

- Events at the end of a time slot:
    1. ``generate_arrival``: Source object generates a part if there is a downstream machine eligible to receive it. 
    2. ``request_space``: Machine with a finished part checks for available space in a downstream buffer or sink.
    3. ``put_part``: If space is available, the machine places a part in the downstream buffer. This event also checks if a starved machine was fed by this action.
    4. ``restore``: A machine has finished maintenance and is restored to a healthier state. Also schedules a maintainer inpection event.
- Events at the beginning of a time slot:
    5. ``degrade``: Machine degrades by one unit. If it is not failed then a time to degrade is sampled and the next degrade event is scheduled. 
    6. ``enter_queue``: If the previous degradation event caused the machine to reach its maintenance threshold then it is placed in the maintenance queue. 
    7. ``fail``: If the previous degradation event caused the machine to reach its failed state, then the machine undergoes failure. 
    8. ``inspect``: Maintaner object inspects the current maintenance queue. If the queue is not empty, the maintainer chooses a machine to repair. Otherwise, the maintainer does nothing. 
    9. ``maintain``: A machine begins maintenance and a restoration event is scheduled after sampling a time to repair. 
    10. ``requeust_part``: An available machine examines upstream buffers and sources for available parts and schedules a retrieval of a part if one is available. 
    11. ``get_part``: A machine retrieves a part from an upstream buffer or source. 
- Simulation run time events:
    12. ``terminate``: The simulation has reached it maximum specified run time and no further events are executed. 

Each simulation event corresponds to a method of the object on which the event takes place. 


Machine Degradation
-------------------

By default, Simantha uses a discrete-time Markov chain (DTMC) to model the degradation process of machines in the system [2]_. The machine will begin in perfect health with a degradation state of 0 and will transition among health states according to the specified degradation transition matrix. A maximum degradation state of :math:`h_{\max}` indicates the failure state of a machine and the resulting size of the transition matrix is therefore :math:`(h_{\max}+1)\times(h_{\max}+1)`. A failed machine must be repaired by a *corrective* maintenance action, whereas a *preventive* maintenance action can be conducted any time before failure. 

Simantha assumes that the degradation transition matrix of each machine is upper triangular. This assumption ensures that a machine cannot transition to a healthier state without the intervention of a maintenance action. Transition matrices of general form are possible under this degradation model, but have not yet been thoroughly tested with Simantha.


Condition-based Maintenance
---------------------------

Simantha allows for the implementation of a condition-based maintenance (CBM) policy that relies on the DTMC degradation process [3]_. A maintenance threshold can be specified which indicates the degradation state index at which preventive maintenance should be performed on a machine. When the degradation state of a machine reaches its threshold, the machine generates a request for maintenance. If maintenance resources are available, maintenance is conducted on the machine. Otherwise, the machine must wait to receive maintenance while continuing to degrade. 


References
----------

.. [1] J. Li and S. M. Meerkov, *Production Systems Engineering*. Springer Science & Business Media, 2008.
.. [2] G. K. Chan and S. Asgarpoor. "Optimum maintenance policy with Markov processes," in *Electric Power Systems Research*, vol. 76.6-7, pp. 452-456, 2006.
.. [3] M. Hoffman, E. Song, M. P. Brundage and S. Kumara, "Online Improvement of Condition-Based Maintenance Policy via Monte Carlo Tree Search," in *IEEE Transactions on Automation Science and Engineering*, 2021.