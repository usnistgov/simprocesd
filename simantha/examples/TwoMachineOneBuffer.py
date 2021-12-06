from .. import Source, Machine, Buffer, Sink, System


def main():
    source = Source()
    M1 = Machine('M1', upstream = [source], cycle_time = 1)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine('M2', upstream = [B1], cycle_time = 1)
    sink = Sink(upstream = [M2])

    system = System([source, M1, B1, M2, sink])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_time = 60 * 24 * 7)


if __name__ == '__main__':
    main()
