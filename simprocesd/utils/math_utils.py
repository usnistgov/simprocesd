import random


def geometric_distribution_sample(probability, target_successes = 1):
    '''How many Bernoulli trials will it take to reach a number of
    successes.

    This function performs random trials based on provided probability.
    Because the trials are random calling the function will same
    parameters does not mean same results.

    Randomness is generated with Python's 'random' module.

    Arguments
    ---------
    probability: float
        Chance of success of each trial (0 to 1).
    target_successes: int, default=1
        Desired number of successes.

    Returns
    -------
    int
        Number of iterations it took to get desired number of successes.
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
