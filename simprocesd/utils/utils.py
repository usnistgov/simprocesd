import csv
import lzma
import os.path

import dill as dill


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


def save_object(obj, file_path, override_file = False):
    ''' Serialize and save an object in a file using Dill module.
    https://pypi.org/project/dill/
    Function also compresses the data using lzma.

    Arguments:
    obj - object that will be serialized
    file_path - relative or absolute path to the file.
    override_file - if True then the function will overwrite an
        existing file at the same path, if False (default) the
        function will fail if provided file already exists.
    '''
    if not override_file and os.path.isfile(file_path):
        raise FileExistsError(f'File \'{file_path}\' already exists.')

    with lzma.open(file_path, 'wb') as file:
        dill.dump(obj, file)


def load_object(file_path):
    '''
    Load an object that was saved using utils.save_object and return
    he loaded object.

    Warning: Only load objects that you trust as they could execute
    arbitrary code.

    Arguments:
    file_path - relative or absolute path to the file.
    '''
    with lzma.open(file_path, 'rb') as file:
        return dill.load(file)

