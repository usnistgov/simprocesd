import random


def geometric_distribution_sample(probability, target_successes):
    ''' Returns the number of iterations before it took to reach target number
    of successes. Randomness is generated with Python's 'random' module.

    Arguments:
    probability -- of success on each trial in percent (0 to 100).
    target_successes -- number of successes.
    '''
    assert probability >= 0 and probability <= 100, 'probability must be 0 to 100'
    trials = 0
    while target_successes > 0:
        trials += 1
        if random.uniform(0, 100) <= probability:
            target_successes -= 1
    return trials
