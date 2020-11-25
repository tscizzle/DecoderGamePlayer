def shiftSamples(samples, desiredRange):
    """Take samples of the interval [0, 1) and shift them as if sampled from some new
    interval.

    :param np.array samples: samples taken from the interval (0, 1]
    :param (float, float) desiredRange: start and end of the interval you want to have
        sampled

    :returns np.array newSamples: shifted samples as if taken from the desired interval
    """
    newSamples = samples * (desiredRange[1] - desiredRange[0]) + desiredRange[0]
    return newSamples
