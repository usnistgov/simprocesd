''' Expected parts produced: 10074
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Source, PartProcessor, Sink


def main():
    system = System()

    source = Source()

    M1 = PartProcessor('M1', upstream = [source], cycle_time = 2)
    M2 = PartProcessor('M2', upstream = [source], cycle_time = 2)
    first_stage = [M1, M2]

    M3 = PartProcessor('M3', upstream = first_stage, cycle_time = 3)
    M4 = PartProcessor('M4', upstream = first_stage, cycle_time = 3)
    M5 = PartProcessor('M5', upstream = first_stage, cycle_time = 3)
    second_stage = [M3, M4, M5]

    M6 = PartProcessor('M6', upstream = second_stage, cycle_time = 2)
    M7 = PartProcessor('M7', upstream = second_stage, cycle_time = 2)

    sink = Sink(upstream = [M6, M7])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
