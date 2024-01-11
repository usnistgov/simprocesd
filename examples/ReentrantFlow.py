'''Expected parts received by sink: 249
Parts flow: source > M1 > M2 > M1 > sink

Note: stage1 and stage3 both use M1 making it possible to get this
setup stuck if source produces parts too fast, this happens when
stage1 and stage2 both have a part to pass downstream. When
stage1-M1 is passing a part to stage2-M2 and stage2-M2 is passing a
part to stage3 which is also M1 this causes a deadlock.
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import Group, PartProcessor, Sink, Source


def main():
    system = System()

    M1 = PartProcessor(name = 'M1', cycle_time = 1)
    M1_group = Group(group_name = 'M1_Group', devices = [M1])

    source = Source(cycle_time = 4)
    stage1 = M1_group.get_new_group_path(name = 'M1_1', upstream = [source])
    stage2 = PartProcessor(name = 'M2', cycle_time = 2, upstream = [stage1])
    stage3 = M1_group.get_new_group_path(name = 'M1_3', upstream = [stage2])
    sink = Sink(upstream = [stage3])

    system.simulate(simulation_duration = 1000)


if __name__ == '__main__':
    main()
