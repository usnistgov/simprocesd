import random


def geometric_distribution_sample(probability, target_successes):
    ''' Returns the number of iterations it took to reach target
    number of successes. Randomness is generated with Python's
    'random' module.

    Arguments:
    probability -- chance of success of each trial (0 to 1).
    target_successes -- number of successes.
    '''
    assert probability >= 0 and probability <= 1, 'probability must be 0 to 1'
    if probability == 0:
        return float('inf')
    elif probability == 1:
        return target_successes

    trials = 0
    while target_successes > 0:
        trials += 1
        if random.uniform(0, 1) < probability:
            target_successes -= 1
    return trials
