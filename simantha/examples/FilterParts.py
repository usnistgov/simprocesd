''' Expected parts produced: 999-1000
Processor should have received 999-1000 parts (same as parts produced).
PartFixer should have received about 750 parts
Processor average output part quality should be around 0.5
PartFixer average output part quality should be around 0.96
'''
import random

from ..model import System
from ..model.factory_floor import Source, Machine, Sink, Filter
from ..model.sensors import OutputPartSensor, AttributeProbe
from ..utils import print_machines_that_received_parts

part_quality_data = {}


def process_part(part):
    part.quality = random.random()


def improve_part(part):
    part.quality = min(1, part.quality + 0.75)


def record_quality(machine, data):
    if machine.name not in part_quality_data.keys():
        part_quality_data[machine.name] = []
    part_quality_data[machine.name].append(data[0])


def main():
    source = Source()

    M1 = Machine('Processor', upstream = [source], cycle_time = 1)
    M1.add_finish_processing_callback(process_part)

    filter1 = Filter(should_pass_part = lambda part: part.quality >= 0.75)
    filter2 = Filter(should_pass_part = lambda part: part.quality < 0.75)

    M2 = Machine('PartFixer', upstream = [filter2], cycle_time = 1)
    M2.add_finish_processing_callback(improve_part)
    filter1.upstream = [M1, M2]
    filter2.upstream = [M1, M2]

    sink = Sink(upstream = [filter1], collect_parts = True)

    # Using sensors to collect part quality data after each machine.
    sensor1 = OutputPartSensor(M1, [AttributeProbe('quality', M1)])
    sensor1.add_on_sense_callback(record_quality)
    sensor2 = OutputPartSensor(M2, [AttributeProbe('quality', M2)])
    sensor2.add_on_sense_callback(record_quality)

    system = System([source, sink, M1, M2, filter1, filter2, sensor1, sensor2])
    random.seed(1)
    system.simulate(simulation_time = 1000)

    # Automatically named machine names start with '<'
    print_machines_that_received_parts(sink.collected_parts, [M1, M2])

    for machine_name, data in part_quality_data.items():
        quality_sum = 0
        for quality in data:
            quality_sum += quality
        average_quality = quality_sum / len(data)
        print(f'Machine {machine_name} average output part quality is {average_quality:.2}')


if __name__ == '__main__':
    main()

