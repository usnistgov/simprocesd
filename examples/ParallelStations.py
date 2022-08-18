''' Expected parts produced: 10074
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Sink


def main():
    system = System()

    source = Source()

    M1 = Machine('M1', upstream = [source], cycle_time = 2)
    M2 = Machine('M2', upstream = [source], cycle_time = 2)
    first_stage = [M1, M2]

    M3 = Machine('M3', upstream = first_stage, cycle_time = 3)
    M4 = Machine('M4', upstream = first_stage, cycle_time = 3)
    M5 = Machine('M5', upstream = first_stage, cycle_time = 3)
    second_stage = [M3, M4, M5]

    M6 = Machine('M6', upstream = second_stage, cycle_time = 2)
    M7 = Machine('M7', upstream = second_stage, cycle_time = 2)

    sink = Sink(upstream = [M6, M7])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
