import csv
import lzma
import os.path

import dill as dill


def assert_is_instance(obj, class_type, message = None):
    '''Check if an object is an instance of a specific class type.

    Arguments
    ---------
    obj: object
        Object that will be checked.
    class_type: type
        Class type that the object needs to be.
    message: str, optional
        Error message if object is not an instance of <class_type>.

    Raises
    ------
    TypeError
        If <obj> is not an instance of <class_type>
    '''
    if not isinstance(obj, class_type):
        if message == None:
            message = f'Object, {type(obj)}, does not implement {class_type}'
        raise TypeError(message)


def assert_callable(obj, none_allowed = False, message = None):
    '''Check if an object appears callable.

    The check is done using the built-in 'callable()' function. In some
    cases it is possible the function not to raise an error even if
    <obj> cannot be called like a function.

    Arguments
    ---------
    obj: object
        Object that will be checked.
    none_allowed: bool, default=False
        If the value of None is allowed.
    message: str, optional
        Error message if object is not callable.

    Raises
    ------
    TypeError
        If object is not callable.
    '''
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


def save_list_to_csv(filename, data_list):
    '''Save a list or table as a CSV file.

    Each list entry will occupy one row and if the list entry is a list
    or a tuple then the entry's elements will be split into columns.

    | Example:
    |    in: data_list = [ [1,2], [3,4,5] ]
    |    file out: Row 1 = 1,2
    |        Row 2 = 3,4,5

    Arguments
    ---------
    filename: str
        Relative or absolute path of where to store the CSV file.
    data_list: list
        Data to be stored, can be a 1 or 2 dimensional list.
    '''
    with open(filename, 'w', newline = '') as file:
        writer = csv.writer(file, quoting = csv.QUOTE_ALL)
        writer.writerows(data_list)


def save_object(obj, file_path, override_file = False):
    '''Serialize, compress, and save an object as a file.

    Uses Dill module to serialize the object.
    https://pypi.org/project/dill/

    Serialized data is compresses using lzma module.

    Arguments
    ---------
    obj: object
        Object to be serialized and stored.
    file_path: str
        Relative or absolute path of where to store the object.
    override_file: bool, default=False
        If True then any existing file at <file_path> will be
        overwritten.

    Raises
    ------
    FileExistsError
        If a file at <file_path> already exists and <override_file> is
        set to False.
    '''
    if not override_file and os.path.isfile(file_path):
        raise FileExistsError(f'File \'{file_path}\' already exists.')

    with lzma.open(file_path, 'wb') as file:
        dill.dump(obj, file)


def load_object(file_path):
    '''Load an object from a file that was created using save_object().

    See save_object() for information on how objects are stored.

    Warning
    -------
    Loaded object could execute arbitrary code when it is loaded.
    Recommended to only load object from files you created or ones from
    a source with a high degree of trust.

    Arguments
    ---------
    file_path: str
        Relative or absolute path to the file to load.
    '''
    with lzma.open(file_path, 'rb') as file:
        return dill.load(file)

