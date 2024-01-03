''' This example sets up machines in series and in parallel. The example
also shows how one machine can be used in multiple places of the
process flow.
See image various_flows_diagram.jpg for a visual representation  of the
setup. Top diagram in the image shows M2 in 2 locations while the bottom
diagram shows the actual Sim-PROCESD setup to represent it.
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, PartProcessor, Sink, DecisionGate
from simprocesd.utils import print_produced_parts_and_average_quality


def main():
    system = System()

    source = Source()

    M1 = PartProcessor('M1', upstream = [source], cycle_time = 2)
    M2 = PartProcessor('M2', upstream = [M1], cycle_time = 5)
    M5 = PartProcessor('M5', upstream = [M1], cycle_time = 5)
    M3 = PartProcessor('M3', upstream = [M2, M5], cycle_time = 0.5)
    # Filters look on the routing history of the part to determine how
    # it got to M2, this determines which way the part is allowed to go.
    G1 = DecisionGate('G1', [M3], lambda gate, part: part.routing_history[-2] == M2)
    G2 = DecisionGate('G2', [M3], lambda gate, part: part.routing_history[-2] == M5)
    M6 = PartProcessor('M6', upstream = [G2], cycle_time = 5)
    M4 = PartProcessor('M4', upstream = [G1, M6], cycle_time = 2)
    machines = [M1, M2, M3, M4, M5, M6]
    sink = Sink(upstream = [M4], collect_parts = True)

    system.simulate(simulation_duration = 1000)
    print_produced_parts_and_average_quality(system, machines)


if __name__ == '__main__':
    main()

