''' Expected parts produced: 20154
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Sink, Batch, PartBatcher, Part


def main():
    system = System()

    parts_per_batch = 5
    source_output = Batch()
    for i in range(parts_per_batch):
        source_output.parts.append(Part())
    # Source will produce a batch of 2 parts every cycle.
    source = Source(cycle_time = 1, sample_part = source_output)

    # Un-batch and process individually.
    M1 = PartBatcher('M1', upstream = [source], output_batch_size = None)
    M2 = Machine('M2', upstream = [M1], cycle_time = 1)
    # Process in batches. Cycle time changed to account for batch size.
    M3 = Machine('M3', upstream = [source], cycle_time = parts_per_batch)

    # M4 ensures individual parts are passed to the sink instead of
    # batches.
    M4 = PartBatcher('M4', upstream = [M2, M3], output_batch_size = None)
    sink = Sink(upstream = [M4])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
