class Cluster(set):
    """
    A Cluster is a set of temporal node occurrences (t, u) representing a subset of W.
    It inherits from python's built-in set class to support all standard set operations.


    Examples
    --------
    >>> from dynetx.classes.cluster import Cluster
    >>> cluster = Cluster()
    >>> cluster.Cluster()
"""
    def __init__(self, iterable=None):
        if iterable is not None:
            super(Cluster, self).__init__(iterable)
        else:
            super(Cluster, self).__init__()

    def add_node(self, t, u):
        """Add a temporal node (t, u) to the cluster.

        Parameters
        ----------
        t : timestamp
        u : node id


        Examples
        --------
        >>> from dynetx.classes.cluster import Cluster
        >>> cluster = Cluster()
        >>> cluster.add_node(0, 1)
"""
        self.add((t, u))

    def remove_node(self, t, u):
        """Remove a temporal node (t, u) from the cluster.

        Parameters
        ----------
        t : timestamp
        u : node id


        Examples
        --------
        >>> from dynetx.classes.cluster import Cluster
        >>> cluster = Cluster()
        >>> cluster.add_node(0, 1)
        >>> cluster.remove_node(0, 1)
"""
        self.remove((t, u))
