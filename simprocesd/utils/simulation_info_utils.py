from matplotlib import pyplot


def print_produced_parts_and_average_quality(system, machines):
    '''Print the number of Parts produced by each machine in the list
    and the Part's average quality.

    Arguments
    ---------
    system: System
        System object used in the simulation.
    machines: list
        List of Machines whose data will be printed.
    '''
    all_production_data = system.simulation_data.get('produced_part', {})
    for machine in machines:
        machine_production_data = all_production_data.get(machine.name, [])
        quality_sum = 0
        for d in machine_production_data:
            quality_sum += d[2]
        try:
            average_quality = round(quality_sum / len(machine_production_data), 4)
        except ZeroDivisionError:
            average_quality = 'N/A'
        print(f'Machine {machine.name} produced {len(machine_production_data)} parts with average '
              +f'quality of {average_quality}')


def print_finished_work_order_counts(system):
    '''Print which machines had work orders completed on them and how
    many of those work orders there were.

    Arguments
    ---------
    system: System
        System object used in the simulation.
    '''
    maintenance_count = {}
    for maintainer_data in system.simulation_data.get('finish_work_order', {}).values():
        for data in maintainer_data:
            if data[1] not in maintenance_count.keys():
                maintenance_count[data[1]] = 1
            else:
                maintenance_count[data[1]] += 1
    for machine_name, count in sorted(maintenance_count.items()):
        print(f'{count} work orders were started and finished on {machine_name}.')


def plot_throughput(system, machines, subplot = None):
    '''Show a graph of cumulative mean throughput over time.

    Cumulative throughput means at time=100 the graph will show the mean
    throughput between time 0 and 100.

    Graph is shown using matplotlib library.

    Arguments
    ---------
    system: System
        System object used in the simulation.
    machines: list
        List of Machines whose data will be plotted.
    subplot: matplotlib.axes.Axes, default = None
        Optional subplot to graph the data on.
        If None then a new figure will be created and shown.
    '''
    is_new_figure, graph = _get_graph(subplot)
    all_production_data = system.simulation_data.get('produced_part', {})
    for machine in machines:
        machine_production_data = all_production_data.get(machine.name, [])
        # Make a list of tuples: (time, parts_produced_so_far)
        production_data = [(machine_production_data[i][0], i + 1)
                           for i in range(len(machine_production_data))]
        throughput = [
            parts_produced / time
            for time, parts_produced in production_data if time != 0
        ]
        graph.plot([d[0] for d in production_data], throughput,
                   lw = 2, label = _format_label(machine_production_data, machine.name))

    graph.set(xlabel = 'time',
              ylabel = 'throughput (units/time_unit)',
              title = 'Throughput',
              xlim = [0, system._env.now])
    graph.legend()
    if is_new_figure:
        pyplot.show()


def plot_damage(system, machines, subplot = None):
    '''Show a graph of damage over time for MachineWithDamage.

    Graph is shown using matplotlib library.

    Arguments
    ---------
    system: System
        System object used in the simulation.
    machines: list
        List of Machines whose damage data will be plotted. One example
        of a Machine that tracks damage is MachineWithDamage.
    subplot: matplotlib.axes.Axes, default = None
        Optional subplot to graph the data on.
        If None then a new figure will be created and shown.
    '''
    is_new_figure, graph = _get_graph(subplot)
    all_damage_data = system.simulation_data.get('damage_update', {})
    for machine in machines:
        damage_data = all_damage_data.get(machine.name, [])
        graph.step([d[0] for d in damage_data],
                   [d[1] for d in damage_data],
                   lw = 2, where = 'post', label = _format_label(damage_data, machine.name))
    graph.set(xlabel = 'time',
              ylabel = 'damage',
              title = 'Machine Damage',
              xlim = [0, system._env.now])
    graph.legend()
    if is_new_figure:
        pyplot.show()


def plot_value(assets, subplot = None):
    '''Show a graph of value over time for any assets.

    Graph is shown using matplotlib library.

    Arguments
    ---------
    assets: list
        List of Assets whose data will be plotted.
    subplot: matplotlib.axes.Axes, default = None
        Optional subplot to graph the data on.
        If None then a new figure will be created and shown.
    '''
    is_new_figure, graph = _get_graph(subplot)
    for asset in assets:
        graph.plot([d[1] for d in asset.value_history],
                   [d[3] for d in asset.value_history],
                   lw = 2,
                   label = asset.name)

    graph.set(xlabel = 'time',
              ylabel = 'Value',
              title = 'Machine Value')
    graph.legend()
    if is_new_figure:
        pyplot.show()


def plot_resources(system, resources, subplot = None, hide_max = False):
    '''Show a graph of active resource usage over time.

    Graph is shown using matplotlib library.

    Arguments
    ---------
    system: System
        System object used in the simulation.
    resources: list
        List of resource names for resources whose data will be plotted.
    subplot: matplotlib.axes.Axes, default = None
        Optional subplot to graph the data on.
        If None then a new figure will be created and shown.
    '''
    is_new_figure, graph = _get_graph(subplot)
    all_resource_data = system.simulation_data.get('resource_update', {})
    for resource_name in resources:
        resource_data = all_resource_data.get(resource_name, [])
        graph.step([d[0] for d in resource_data],
                            [d[1] for d in resource_data],
                            lw = 2, where = 'post', label = _format_label(resource_data, resource_name))
        if not hide_max:
            graph.step([d[0] for d in resource_data],
                                [d[2] for d in resource_data],
                                lw = 2, where = 'post', color = 'r', linestyle = 'dashed')
    graph.set(xlabel = 'time',
              ylabel = 'usage',
              title = 'Resource Usage',
              xlim = [0, system._env.now])
    graph.legend()
    if is_new_figure:
        pyplot.show()


def plot_buffer_levels(system, buffers, subplot = None):
    '''Show a graph of Buffer levels over time.

    Graph is shown using matplotlib library.

    Arguments
    ---------
    system: System
        System object used in the simulation.
    buffers: list
        List of Buffers whose data will be plotted.
    subplot: matplotlib.axes.Axes, default = None
        Optional subplot to graph the data on.
        If None then a new figure will be created and shown.
    '''
    is_new_figure, graph = _get_graph(subplot)
    all_level_data = system.simulation_data.get('level', {})
    for buffer in buffers:
        level_data = all_level_data.get(buffer.name, [])
        graph.step([d[0] for d in level_data],
                   [d[1] for d in level_data],
                   lw = 2, where = 'post', label = _format_label(level_data, buffer.name))
    graph.set(xlabel = 'time',
              ylabel = 'level',
              title = 'Buffer Level',
              xlim = [0, system._env.now])
    graph.legend()
    if is_new_figure:
        pyplot.show()


def simple_plot(x, y, title = '', xlabel = '', ylabel = '',
                data_label = None, fmt = None, subplot = None):
    '''Show a graph with a single plot from the provided data.

    Arguments
    ---------
    x: list
        List of x values.
    y: list
        List of y values, must be same length as <x>.
    title: str, optional
        Graph title.
    data_label:
        Label for the data being graphed.
    fmt: string, default = None
        Format string that defines the appearance of the line.
        See matplotlib.pyplot.plot documentation for more information.
    subplot: matplotlib.axes.Axes, default = None
        Optional subplot to graph the data on.
        If None then a new figure will be created and shown.
    '''
    is_new_figure, graph = _get_graph(subplot)
    graph_kwargs = {}
    graph_args = [x, y]
    if data_label != None:
        graph_kwargs['label'] = _format_label(x, data_label)
    if fmt != None:
        graph_args.append(fmt)
    graph.plot(*graph_args, **graph_kwargs)
    graph.set(xlabel = xlabel,
              ylabel = ylabel,
              title = title,
              xlim = [0, x[-1]])
    if is_new_figure:
        pyplot.show()


def _get_graph(provided_graph = None):
    if provided_graph == None:
        figure, resource_graph = pyplot.subplots()
        figure.canvas.manager.set_window_title('Close window to continue.')
        new_fig = True
    else:
        resource_graph = provided_graph
        new_fig = False
    return (new_fig, resource_graph)


def _format_label(data, label):
    if len(data) == 0:
        return label + '(no data)'
    else:
        return label
