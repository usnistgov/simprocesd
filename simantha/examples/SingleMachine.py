from .. import Source, Machine, Sink, System, Part


def main():
    part = Part()
    source = Source(part)
    M1 = Machine(name = 'M1', upstream = [source], cycle_time = 1)
    sink = Sink(upstream = [M1])

    system = System(objects = [source, M1, sink])

    system.simulate(simulation_time = 100)
    print(f'Sink received {sink.received_parts_count} parts.')


if __name__ == '__main__':
    main()
