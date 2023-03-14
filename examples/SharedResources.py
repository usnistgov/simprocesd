''' Expected parts produced: about 2016

5 time units to process a part by any path.
Total runtime is 10080 time units.
Only one Machine can be active at once due to the 'operator' limit.
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Sink


def main():
    system = System()
    system.resource_manager.add_resources('tool', 5)
    system.resource_manager.add_resources('operator', 1)

    source = Source()

    needed_resources = {'operator': 1, 'tool': 1}
    M1 = Machine('M1', upstream = [source], cycle_time = 2, resources_for_processing = needed_resources)
    M2 = Machine('M2', upstream = [source], cycle_time = 2, resources_for_processing = needed_resources)
    first_stage = [M1, M2]

    M3 = Machine('M3', upstream = first_stage, cycle_time = 3, resources_for_processing = needed_resources)
    M4 = Machine('M4', upstream = first_stage, cycle_time = 3, resources_for_processing = needed_resources)
    M5 = Machine('M5', upstream = first_stage, cycle_time = 3, resources_for_processing = needed_resources)
    sink = Sink(upstream = [M3, M4, M5])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
