''' Expected parts received by sink: 97
M01 should receive 100 parts.
M02 should receive 99 parts.
M03 and M04 should not receive any parts.
M05, M06, and M07 should each receive 33, 33, and 32 parts respectively.
M08, M09, and M10 use random distribution will and likely have similar
received part counts. Change n in random.seed(n) to get a different
random distribution.
'''
import random

from ..model import System
from ..model.factory_floor import Source, Machine, Sink, PartHandlingDevice, FlowOrder
from ..utils import DataStorageType, print_produced_parts_and_average_quality


def main():
    random.seed(5)
    source = Source()

    M1 = Machine('M01', upstream = [source], cycle_time = 1)

    phd1 = PartHandlingDevice(upstream = [M1], flow_order = FlowOrder.FIRST_AVAILABLE)
    M2 = Machine('M02', upstream = [phd1], cycle_time = 1)
    M3 = Machine('M03', upstream = [phd1], cycle_time = 1)
    M4 = Machine('M04', upstream = [phd1], cycle_time = 1)
    stage_1 = [M2, M3, M4]
    # Set downstream manually to ensure list order where M02 is first.
    phd1.set_downstream_order(stage_1)

    phd2 = PartHandlingDevice(upstream = stage_1, flow_order = FlowOrder.ROUND_ROBIN)
    M5 = Machine('M05', upstream = [phd2], cycle_time = 1)
    M6 = Machine('M06', upstream = [phd2], cycle_time = 1)
    M7 = Machine('M07', upstream = [phd2], cycle_time = 1)
    stage_2 = [M5, M6, M7]

    phd3 = PartHandlingDevice(upstream = stage_2, flow_order = FlowOrder.RANDOM)
    M8 = Machine('M08', upstream = [phd3], cycle_time = 1)
    M9 = Machine('M09', upstream = [phd3], cycle_time = 1)
    M10 = Machine('M10', upstream = [phd3], cycle_time = 1)
    stage_3 = [M8, M9, M10]

    sink = Sink(upstream = stage_3, collect_parts = True)

    machines = [M1] + stage_1 + stage_2 + stage_3
    system = System([source, sink, phd1, phd2, phd3] + machines, DataStorageType.MEMORY)
    system.simulate(simulation_time = 100)

    print_produced_parts_and_average_quality(system, machines)


if __name__ == '__main__':
    main()

