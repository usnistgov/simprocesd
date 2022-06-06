''' This example sets up machines in series and in parallel. The example
also shows how one machine can be used in multiple places of the
process flow.
See image various_flows_diagram.jpg for a visual representation  of the
setup. Top diagram in the image shows M2 in 2 locations while the bottom
diagram shows the actual Simantha setup to represent it.
'''

from simantha.model import System
from simantha.model.factory_floor import Source, Machine, Sink, Filter
from simantha.utils import DataStorageType, print_produced_parts_and_average_quality


def main():
    system = System(DataStorageType.MEMORY)

    source = Source()

    M1 = Machine('M1', upstream = [source], cycle_time = 2)
    M2 = Machine('M2', upstream = [M1], cycle_time = 5)
    M5 = Machine('M5', upstream = [M1], cycle_time = 5)
    M3 = Machine('M3', upstream = [M2, M5], cycle_time = 0.5)
    # Filters look on the routing history of the part to determine how
    # it got to M2, this determines which way the part is allowed to go.
    F1 = Filter(lambda part: part.routing_history[-2] == M2, 'F1', [M3])
    F2 = Filter(lambda part: part.routing_history[-2] == M5, 'F2', [M3])
    M6 = Machine('M6', upstream = [F2], cycle_time = 5)
    M4 = Machine('M4', upstream = [F1, M6], cycle_time = 2)
    machines = [M1, M2, M3, M4, M5, M6]
    sink = Sink(upstream = [M4], collect_parts = True)

    system.simulate(simulation_time = 1000)
    print_produced_parts_and_average_quality(system, machines)


if __name__ == '__main__':
    main()

