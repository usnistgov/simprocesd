import random


def geometric_distribution_sample(probability, target_successes):
    trials = 0
    while target_successes > 0:
        trials += 1
        if random.uniform(0, 100) <= probability:
            target_successes -= 1
    return trials
