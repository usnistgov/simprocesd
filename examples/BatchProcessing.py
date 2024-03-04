''' Expected parts produced: 10075
Sink is receiving Batch parts but tracks how many individual parts it
received.
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Source, PartProcessor, Sink, Batch, PartBatcher, Part, PartGenerator


class CustomPartGenerator(PartGenerator):

    def __init__(self, parts_per_batch):
        super().__init__('CustomBatch')
        self.parts_per_batch = parts_per_batch

    # Override for PartGenerator.generate_part_helper
    def generate_part_helper(self, part_name, part_counter):
        batch = Batch(name = part_name)
        for i in range(self.parts_per_batch):
            batch.parts.append(Part())
        return batch


def main():
    system = System()

    parts_per_batch = 5
    # Source will produce a batch parts every cycle.
    source = Source(cycle_time = 1, part_generator = CustomPartGenerator(parts_per_batch))

    # Path 1: Unbatch, process individually, and batch parts together again.
    M1 = PartBatcher('M1', upstream = [source], output_batch_size = None)
    M2 = PartProcessor('M2', upstream = [M1], cycle_time = 1)
    M3 = PartBatcher('M3', upstream = [M2], output_batch_size = parts_per_batch)
    # Path 2: Process in batches. Cycle time changed to account for batch size.
    M4 = PartProcessor('M4', upstream = [source], cycle_time = parts_per_batch)

    sink = Sink(upstream = [M3, M4])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
