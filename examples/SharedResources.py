''' Expected parts produced: 6046

5 time units to process a part by any path.
Total runtime is 10080 time units and there are 3 operators.
Approximate expected result: 10080 * 3 / 5 = 6048
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Buffer, Machine, Sink, Source


def main():
    system = System()
    system.resource_manager.add_resources('tool1', 2)
    system.resource_manager.add_resources('tool2', 2)
    system.resource_manager.add_resources('operator', 3)

    source = Source()

    needed_resources1 = {'operator': 1, 'tool1': 1}
    needed_resources2 = {'operator': 1, 'tool2': 1}
    M1 = Machine('M1', upstream = [source], cycle_time = 2, resources_for_processing = needed_resources1)
    M2 = Machine('M2', upstream = [source], cycle_time = 2, resources_for_processing = needed_resources1)
    B1 = Buffer('B1', [M1, M2], capacity = 5)

    M3 = Machine('M3', upstream = [B1], cycle_time = 3, resources_for_processing = needed_resources2)
    M4 = Machine('M4', upstream = [B1], cycle_time = 3, resources_for_processing = needed_resources2)
    sink = Sink(upstream = [M3, M4])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
