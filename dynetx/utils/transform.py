__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

__all__ = [
    'clean_timeslot',
]


def clean_timeslot(sind_list):
    tls = sorted(sind_list)
    conversion = {val: idx for idx, val in enumerate(tls)}
    return conversion



