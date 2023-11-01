''' Expected parts produced: 720.
M1 operates for 8 of the 24 hours (see <schedule>). When the schedule
state is set to True then M1 can receive new Parts to process.
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import ActionScheduler, PartProcessor, Part, Sink, Source


class MachineSchedule(ActionScheduler):

    def default_action(self, machine, time, is_working):
        machine.block_input = not is_working


def main():
    system = System()
    # 4 hours on, 0.5 hours off, 4 hours on, and 15.5 hours off.
    schedule = MachineSchedule([(4, True), (0.5, False), (4, True), (15.5, False)])

    source = Source(sample_part = Part())
    M1 = PartProcessor(upstream = [source], cycle_time = 0.333)
    schedule.register_object(M1)
    sink = Sink(upstream = [M1])

    system.simulate(simulation_duration = 24 * 30)


if __name__ == '__main__':
    main()
