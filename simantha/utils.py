"""
The ``utils`` module provides convenient utility functions and useful constants. 
Although the constants are given in minutes, a single simulation time unit can 
theoretically represent any duration of time. 
"""


def generate_degradation_matrix(p, h_max):
    """
    Generate an upper triangular degradation transition matrix.


    Parameters
    ----------
    p : float
        The probability of degrading by one unit at each time step.
    h_max : int
        The index of the failed state.


    Returns
    -------
    list of lists
        A ``(h_max + 1)`` :math:`\\times` ``(h_max + 1)`` degradation transition matrix.

    """
    degradation_matrix = []
    for h in range(h_max):
        transitions = [0] * (h_max + 1)
        transitions[h] = 1 - p
        transitions[h + 1] = p
        degradation_matrix.append(transitions)
    degradation_matrix.append([0] * h_max + [1])
    return degradation_matrix


def assert_is_instance(obj, type_):
    if not isinstance(obj, type_):
        raise TypeError(f"Object, {type(obj)}, is not and does not implement {type_}")
