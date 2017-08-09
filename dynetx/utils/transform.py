__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

__all__ = [
    'compact_timeslot',
]


# @todo: define remapping snapshot methods
def compact_timeslot(sind_list):
    """
    Test method. Compact all snapshots into a single one.

    :param sind_list:
    :return:
    """
    tls = sorted(sind_list)
    conversion = {val: idx for idx, val in enumerate(tls)}
    return conversion



