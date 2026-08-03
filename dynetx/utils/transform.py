__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

__all__ = [
    'compact_timeslot',
]


def compact_timeslot(sind_list):
    """Remap sparse snapshot identifiers to a compact zero-based index.

    Parameters
    ----------
    sind_list : iterable
        Iterable of snapshot identifiers.

    Returns
    -------
    dict
        Mapping from the original snapshot identifiers to contiguous indices.

    Examples
    --------
    >>> from dynetx.utils.transform import compact_timeslot
    >>> compact_timeslot([10, 20, 30])
    {10: 0, 20: 1, 30: 2}
    """
    tls = sorted(sind_list)
    conversion = {val: idx for idx, val in enumerate(tls)}
    return conversion


