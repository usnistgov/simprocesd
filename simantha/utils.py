"""
The ``utils`` module provides convenient utility functions and useful constants. 
Although the constants are given in minutes, a single simulation time unit can 
theoretically represent any duration of time. 
"""


def assert_is_instance(obj, type_, message = None):
    if not isinstance(obj, type_):
        if message == None:
            message = f"Object, {type(obj)}, does not implement {type_}"
        raise TypeError(message)


def assert_callable(obj, none_allowed = False, message = None):
    if obj == None:
        if not none_allowed:
            message = f"obj can not be None."
            raise TypeError(message)
    elif not callable(obj):
        if none_allowed:
            message = f"Object, {type(obj)}, must be a callable or None."
        else:
            message = f"Object, {type(obj)}, must be a callable."
        raise TypeError(message)
