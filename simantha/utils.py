"""
The ``utils`` module provides convenient utility functions and useful constants. 
Although the constants are given in minutes, a single simulation time unit can 
theoretically represent any duration of time. 
"""


def assert_is_instance(obj, type_):
    if not isinstance(obj, type_):
        raise TypeError(f"Object, {type(obj)}, is not and does not implement {type_}")
