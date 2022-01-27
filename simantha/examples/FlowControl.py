''' Expected parts produced: 97
M02 should receive 97 parts while M03 and M04 should not receive any.
M05, M06, and M07 should all have received almost the same number of
parts, within 1 of each other.
M08, M09, and M10 use random distribution will and likely have similar
received part counts. Change n in random.seed(n) to get a different
random distribution.
'''
import random

from ..model.factory_floor import Source, Machine, Sink, PartHandlingDevice, FlowOrder
from ..model import System
from ..utils import print_machines_that_received_parts


def main():
    source = Source()

    M1 = Machine('M01', upstream = [source], cycle_time = 1)

    phd1 = PartHandlingDevice(upstream = [M1], flow_order = FlowOrder.FIRST_AVAILABLE)
    M2 = Machine('M02', upstream = [phd1], cycle_time = 1)
    M3 = Machine('M03', upstream = [phd1], cycle_time = 1)
    M4 = Machine('M04', upstream = [phd1], cycle_time = 1)
    stage_1 = [M2, M3, M4]
    # Set downstream manually to ensure list order where M02 is first.
    phd1.set_downstream(stage_1)

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

    system = System([source, sink, M1, phd1, phd2, phd3] + stage_1 + stage_2 + stage_3)
    random.seed(5)
    system.simulate(simulation_time = 100)

    print_machines_that_received_parts(sink.collected_parts, lambda n: n[0] == 'M')


if __name__ == '__main__':
    main()

