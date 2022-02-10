from matplotlib import pyplot


def print_machines_that_received_parts(parts, machines):
    ''' Prints machines through which the given parts have passed and
    how many times the following parts passed through those machines.

    Arguments:
    parts -- parts which passed through machines.
    machines -- list of Machine objects.
    '''
    machine_names = [m.name for m in machines]
    part_counter = {mn: 0 for mn in machine_names}
    for p in parts:
        for r in p.routing_history:
            if r in machine_names:
                part_counter[r] += 1

    for name, count in part_counter.items():
        print(f'Machine {name} received {count} of the parts.')


def print_produced_parts_and_average_quality(system, machines):
    ''' Prints number of parts produced by all machines or machines in
    the list if provided. Also prints average quality of produced parts.

    Arguments:
    system -- System object used in the simulation.
    machines -- list of Machine objects.
    '''
    for machine in machines:
        machine_production_data = system.simulation_data['produced_parts'].get(machine.name, [])
        quality_sum = 0
        for d in machine_production_data:
            quality_sum += d[1]
        average_quality = quality_sum / len(machine_production_data)
        print(f'Machine {machine.name} produced {len(machine_production_data)} parts with average '
              +f'quality of {average_quality:.4}')


def plot_throughput(system, machines):
    ''' Shows a graph of accumulated throughput over accumulated time
    for provided machines.

    Arguments:
    system -- System object used in the simulation.
    machines -- list of Machine objects.
    '''
    for machine in machines:
        produced_parts = system.simulation_data['produced_parts'].get(machine.name, [])
        # List of tuples: (time, parts_produced_so_far)
        production_data = [(produced_parts[i][0], i + 1) for i in range(len(produced_parts))]
        throughput = [
            parts_produced / time
            for time, parts_produced in production_data if time != 0
        ]
        pyplot.plot([d[0] for d in production_data], throughput, lw = 2, label = machine.name)

    pyplot.title('Throughput')
    pyplot.xlabel('time')
    pyplot.ylabel('throughput (units/time_unit)')
    pyplot.xlim([0, system._env.now])
    pyplot.legend()
    pyplot.show()


def plot_damage(system, machines):
    ''' Shows a graph with a step function of damage over time for each
    machine if such data is available.

    Arguments:
    system -- System object used in the simulation.
    machines -- list of Machine objects.
    '''
    pyplot.figure(figsize = (8, 5))
    for machine in machines:
        damage_data = system.simulation_data['damage_update'].get(machine.name, [])
        pyplot.step([d[0] for d in damage_data],
                    [d[1] for d in damage_data],
                    lw = 2, where = 'post', label = machine.name)
    pyplot.xlabel('time')
    pyplot.ylabel('machine damage')
    pyplot.xlim([0, system._env.now])
    pyplot.legend()
    pyplot.show()


def plot_value(assets):
    ''' Shows a graph of value over time for provided assets.

    Arguments:
    system -- System object used in the simulation.
    assets -- list of Asset objects.
    '''
    for asset in assets:
        sum_ = []
        current = 0
        for d in asset.value_history:
            current += d[2]
            sum_.append(current)
        pyplot.plot([d[1] for d in asset.value_history],
                    [d for d in sum_],
                    lw = 2,
                    label = asset.name)

    pyplot.title('Value over time')
    pyplot.xlabel('time')
    pyplot.ylabel('Value')
    pyplot.legend()
    pyplot.show()
