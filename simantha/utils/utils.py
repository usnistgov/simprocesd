import csv


def assert_is_instance(obj, type_, message = None):
    if not isinstance(obj, type_):
        if message == None:
            message = f'Object, {type(obj)}, does not implement {type_}'
        raise TypeError(message)


def assert_callable(obj, none_allowed = False, message = None):
    if obj == None:
        if not none_allowed:
            message = f'obj can not be None.'
            raise TypeError(message)
    elif not callable(obj):
        if none_allowed:
            message = f'Object, {type(obj)}, must be a callable or None.'
        else:
            message = f'Object, {type(obj)}, must be a callable.'
        raise TypeError(message)


def save_list_to_csv(filename, list_):
    ''' Save a file with named <filename> in the current directory and fill it
    with CVS data from list_. Each list entry will occupy one row and if the
    list entry is a list or a tuple then the entry will be split into columns.
    Example:
        list_ = [(1,2),(3,4,5)]
        File contents: 1,2
                       3,4,5
    '''
    with open(filename, 'w', newline = '') as file:
        writer = csv.writer(file, quoting = csv.QUOTE_ALL)
        writer.writerows(list_)
