''' In this example there are two main production paths with different
inputs and outputs. Both paths share one machine.

User can configure settings to see how it affects production:
- operator schedule: how many operators are available and when
- machine schedule: when (day/night/both) can each machine operate
- buffer size
- maximum available power at any given time
- duration of the simulation

At the end of the simulation user is presented with graphs to help
evaluate the effectiveness of the current configuration.
'''
import sys

from simprocesd.model import System
from simprocesd.model.factory_floor import ActionScheduler, Buffer, DecisionGate, PartProcessor, \
    Sink, Source
from simprocesd.utils.simulation_info_utils import plot_buffer_levels, plot_resources
from random import random
from matplotlib import pyplot


class MachineSchedule(ActionScheduler):

    def default_action(self, machine, time, is_working):
        machine.block_input = not is_working


class OperatorSchedule(ActionScheduler):

    def default_action(self, resource_manager, time, new_limit):
        current_total = resource_manager.get_resource_capacity('operators')
        resource_manager.add_resources('operators', new_limit - current_total)


def M3_process(machine, part):
    part.quality = 1


def M4_process(machine, part):
    part.quality = random()  # 0 to 1


def main(is_test = False):
    system = System()

    # Setting maximum available power at any given time.
    system.resource_manager.add_resources('power', 500000)

    # M2 is setup as two separate machines that both require this
    # resource to operate meaning only one of them can be processing
    # parts at any given time. If the value is changed to 2 that
    # represents having 2 of this type of machine that can both be
    # processing at once.
    system.resource_manager.add_resources('shared_machine_M2', 1)

    system.resource_manager.add_resources('operators', 4)
    # 4 operators available for 8 hours and then 3 for 16 hours.
    # This schedule cycles, 24 hour schedule.
    operator_schedule = OperatorSchedule([(8 * 60, 4), (16 * 60, 3)])
    operator_schedule.register_object(system.resource_manager)

    # Buffer size for all buffers. Each buffer's limit can be
    # configured independently further down.
    buffer_limit = 50

    source1 = Source()
    M1 = PartProcessor('M1', upstream = [source1], cycle_time = 16,
                       resources_for_processing = {'operators': 1, 'power': 11000})
    M2_1 = PartProcessor('M2', upstream = [M1], cycle_time = 23,
                         resources_for_processing = {'operators': 1, 'power': 165000, 'shared_machine_M2': 1})
    B1 = Buffer('B1', upstream = [M2_1], capacity = buffer_limit)
    M3 = PartProcessor('M3', upstream = [B1], cycle_time = 7,
                       resources_for_processing = {'operators': 1, 'power': 43000})
    M3.add_finish_processing_callback(M3_process)
    B2 = Buffer('B2', upstream = [M3], capacity = buffer_limit)
    M4 = PartProcessor('M4', upstream = [B2], cycle_time = 12,
                       resources_for_processing = {'operators': 1, 'power': 95000})
    M4.add_finish_processing_callback(M4_process)
    gate1 = DecisionGate(should_pass_part = lambda g, part: part.quality < 0.8, upstream = [M4])
    gate2 = DecisionGate(should_pass_part = lambda g, part: part.quality >= 0.8, upstream = [M4])
    B1.set_upstream(B1.upstream + [gate1])
    sink1 = Sink('Sink1', upstream = [gate2])

    source2 = Source()
    M5 = PartProcessor('M1', upstream = [source2], cycle_time = 14,
                       resources_for_processing = {'operators': 1, 'power': 37000})
    B3 = Buffer('B3', upstream = [M5], capacity = buffer_limit)
    M2_2 = PartProcessor('M2', upstream = [B3], cycle_time = 13,
                         resources_for_processing = {'operators': 1, 'power': 165000, 'shared_machine_M2': 1})
    B4 = Buffer('B4', upstream = [M2_2], capacity = buffer_limit)
    M6 = PartProcessor('M6', upstream = [B4], cycle_time = 9,
                       resources_for_processing = {'operators': 1, 'power': 29000})
    sink2 = Sink('Sink2', upstream = [M6])

    # Two 8 hours shift schedules and one that is both.
    # True = on, False = off.
    schedule_morning = MachineSchedule([(8 * 60, True), (16 * 60, False)])
    schedule_evening = MachineSchedule([(9 * 60, False), (8 * 60, True), (7 * 60, False)])
    schedule_both = MachineSchedule([(8 * 60, True), (1 * 60, False), (8 * 60, True), (7 * 60, False)])

    # During which shift(s) can a machine operate.
    schedule_morning.register_object(M1)
    schedule_morning.register_object(M2_1)
    schedule_both.register_object(M3)
    schedule_both.register_object(M4)
    schedule_morning.register_object(M5)
    schedule_evening.register_object(M2_2)
    schedule_evening.register_object(M6)

    # Time units are minutes and the simulation period is one week.
    system.simulate(simulation_duration = 60 * 24 * 7)
    print(f'{sink1.name} received: {sink1.received_parts_count}')
    print(f'{sink2.name} received: {sink2.received_parts_count}')

    if not is_test:
        # Prepare and show graphs.
        fig, (g1, g2, g3) = pyplot.subplots(3)
        fig.suptitle('Results')
        plot_buffer_levels(system, [B1, B2, B3, B4], g1)
        plot_resources(system, ['power'], g2, hide_max = True)
        plot_resources(system, ['operators'], g3)
        pyplot.show()


if __name__ == '__main__':
    main(len(sys.argv) > 1 and sys.argv[1] == 'testing')
