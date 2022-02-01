

def print_machines_that_received_parts(parts, filter_ = lambda machine_name: True):
    ''' Prints machines through which the given parts have passed and
    how many times the following parts passed through those machines.

    Arguments:
    parts -- parts which passed through machines.
    filter_ -- function that returns where the given machine name should
        be printed (True) or skipped (False).
    '''
    part_counter = {}
    for p in parts:
        for r in p.routing_history:
            part_counter[r] = part_counter.get(r, 0) + 1

    for name, count in sorted(part_counter.items()):
        if filter_(name):
            print(f'Machine {name} received {count} of the parts.')

