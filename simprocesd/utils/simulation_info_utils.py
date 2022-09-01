from matplotlib import pyplot


def print_produced_parts_and_average_quality(system, machines):
    ''' Prints number of parts produced by all machines or machines in
    the list if provided. Also prints average quality of produced parts.

    Arguments:
    system -- System object used in the simulation.
    machines -- list of Machine objects.
    '''
    all_production_data = system.simulation_data.get('produced_parts', {})
    for machine in machines:
        machine_production_data = all_production_data.get(machine.name, [])
        quality_sum = 0
        for d in machine_production_data:
            quality_sum += d[1]
        try:
            average_quality = round(quality_sum / len(machine_production_data), 4)
        except ZeroDivisionError:
            average_quality = 'N/A'
        print(f'Machine {machine.name} produced {len(machine_production_data)} parts with average '
              +f'quality of {average_quality}')


def print_maintenance_counts(system):
    ''' Prints which machines were maintained and how many maintenances
    of those machines were completed.

    Arguments:
    system -- System object used in the simulation.
    '''
    maintenance_count = {}
    for maintainer_data in system.simulation_data.get('finish_maintenance', {}).values():
        for data in maintainer_data:
            if data[1] not in maintenance_count.keys():
                maintenance_count[data[1]] = 1
            else:
                maintenance_count[data[1]] += 1
    for machine_name, count in sorted(maintenance_count.items()):
        print(f'{machine_name} was maintained {count} times.')


def plot_throughput(system, machines):
    ''' Shows a graph of accumulated throughput over accumulated time
    for provided machines.

    Arguments:
    system -- System object used in the simulation.
    machines -- list of Machine objects.
    '''
    figure, graph = pyplot.subplots()
    all_production_data = system.simulation_data.get('produced_parts', {})
    for machine in machines:
        machine_production_data = all_production_data.get(machine.name, [])
        # Make a list of tuples: (time, parts_produced_so_far)
        production_data = [(machine_production_data[i][0], i + 1)
                           for i in range(len(machine_production_data))]
        throughput = [
            parts_produced / time
            for time, parts_produced in production_data if time != 0
        ]
        graph.plot([d[0] for d in production_data], throughput, lw = 2, label = machine.name)

    figure.canvas.manager.set_window_title('Close window to continue.')
    graph.set(xlabel = 'time',
              ylabel = 'throughput (units/time_unit)',
              title = 'Throughput',
              xlim = [0, system._env.now])
    graph.legend()
    pyplot.show()


def plot_damage(system, machines):
    ''' Shows a graph with a step function of damage over time for each
    machine if such data is available.

    Arguments:
    system -- System object used in the simulation.
    machines -- list of Machine objects.
    '''
    figure, graph = pyplot.subplots()
    all_damage_data = system.simulation_data.get('damage_update', {})
    for machine in machines:
        damage_data = all_damage_data.get(machine.name, [])
        graph.step([d[0] for d in damage_data],
                   [d[1] for d in damage_data],
                   lw = 2, where = 'post', label = machine.name)
    figure.canvas.manager.set_window_title('Close window to continue.')
    graph.set(xlabel = 'time',
              ylabel = 'damage',
              title = 'Machine Damage',
              xlim = [0, system._env.now])
    graph.legend()
    pyplot.show()


def plot_value(assets):
    ''' Shows a graph of value over time for provided assets.

    Arguments:
    assets -- list of Asset objects.
    '''
    figure, graph = pyplot.subplots()
    for asset in assets:
        graph.plot([d[1] for d in asset.value_history],
                   [d[3] for d in asset.value_history],
                   lw = 2,
                   label = asset.name)

    figure.canvas.manager.set_window_title('Close window to continue.')
    graph.set(xlabel = 'time',
              ylabel = 'Value',
              title = 'Machine Value')
    graph.legend()
    pyplot.show()


def simple_plot(x, y, title = '', xlabel = '', ylabel = ''):
    figure, graph = pyplot.subplots()
    graph.plot(x, y)
    figure.canvas.manager.set_window_title('Close window to continue.')
    graph.set(xlabel = xlabel,
              ylabel = ylabel,
              title = title,
              xlim = [0, x[-1]])
    pyplot.show()
