''' Example of saving the system object to a file and then loading
it back. Same methods can be used to store and load almost any Python
object.
System object contains all of the devices used in the simulation and
all of the collected data so far.
'''

import os

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Sink
from simprocesd.utils import save_object, load_object


def main():
    file_name = 'SystemSimulation.save'

    system = System()
    source = Source()
    M1 = Machine('Machine', [source], 1)
    sink = Sink(upstream = [M1])

    system.simulate(simulation_duration = 100)

    loaded_system = None
    try:
        save_object(system, file_name)
        loaded_system = load_object(file_name)
    finally:
        os.remove(file_name)

    machines = loaded_system.find_assets(type_ = Machine)
    print(f'Machines from loaded system: {[m.name for m in machines]}')


if __name__ == '__main__':
    main()
