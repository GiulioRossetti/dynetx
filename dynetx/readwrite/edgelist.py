"""
Read and write DyNetx graphs as edge lists.

The multi-line adjacency list format is useful for graphs with nodes
that can be meaningfully represented as strings.

With the edgelist format simple edge data can be stored but node or graph data is not.
There is no way of representing isolated nodes unless the node has a self-loop edge.

Format
------
You can read or write three formats of edge lists with these functions.

Node pairs with **timestamp** (u, v, t):

>>> 1 2 0

Sequence of **Interaction** events (u, v, +/-, t):

>>> 1 2 + 0
>>> 1 2 - 3
"""

from dynetx.utils import open_file, make_str, compact_timeslot
from dynetx import DynGraph
from dynetx import DynDiGraph

__author__ = 'Giulio Rossetti'
__license__ = "BSD-Clause-2"
__email__ = "giulio.rossetti@gmail.com"

__all__ = ['write_interactions',
           'generate_interactions',
           'parse_interactions',
           'read_interactions',
           'generate_snapshots',
           'write_snapshots',
           'parse_snapshots',
           'read_snapshots']


def generate_interactions(G, delimiter=' '):
    for e in G.stream_interactions():
        yield delimiter.join(map(make_str, e))


@open_file(1, mode='wb')
def write_interactions(G, path, delimiter=' ', encoding='utf-8'):
    """Write a DyNetx graph in interaction list format.


        Parameters
        ----------

        G : graph
            A DyNetx graph.

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter

        encoding: str
            Text enconding, default utf-8
        """
    for line in generate_interactions(G, delimiter):
        line += '\n'
        path.write(line.encode(encoding))


@open_file(0, mode='rb')
def read_interactions(path, comments="#", directed=False, delimiter=None,
                      nodetype=None, timestamptype=None, encoding='utf-8', keys=False):
    """Read a DyNetx graph from interaction list format.


        Parameters
        ----------

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter

        comments: character
            Comments row identifier

        directed: bool
            Whether the graph is directed or not

        nodetype: object
            node type

        timestamptype: object
            timestamp type

        encoding: str
            File encoding, default utf-8

        keys: bool

    """
    ids = None
    lines = (line.decode(encoding) for line in path)
    if keys:
        ids = read_ids(path.name, delimiter=delimiter, timestamptype=timestamptype)

    return parse_interactions(lines, comments=comments, directed=directed, delimiter=delimiter, nodetype=nodetype,
                              timestamptype=timestamptype, keys=ids)


def parse_interactions(lines, comments='#', directed=False, delimiter=None, nodetype=None, timestamptype=None,
                       keys=None):
    if not directed:
        G = DynGraph()
    else:
        G = DynDiGraph()

    for line in lines:

        p = line.find(comments)
        if p >= 0:
            line = line[:p]
        if not len(line):
            continue

        s = line.strip().split(delimiter)

        if len(s) != 4:
            continue
        else:
            u = s.pop(0)
            v = s.pop(0)
            op = s.pop(0)
            s = s.pop(0)

        if nodetype is not None:
            try:
                u = nodetype(u)
                v = nodetype(v)
            except:
                raise TypeError("Failed to convert nodes %s,%s to type %s." % (u, v, nodetype))

        if timestamptype is not None:
            try:
                s = timestamptype(s)
            except:
                raise TypeError("Failed to convert timestamp %s to type %s." % (s, nodetype))

        if keys is not None:
            s = keys[s]

        if op == '+':
            G.add_interaction(u, v, t=s)
        else:
            timestamps = G.adj[u][v]['t']
            if len(timestamps) > 0 and timestamps[-1][1] < s:
                for t in range(timestamps[-1][1], s):
                    G.add_interaction(u, v, t=t)

    return G


def generate_snapshots(G, delimiter=' '):
    for u, v, d in G.interactions():
        if 't' not in d:
            raise NotImplemented
        for t in d['t']:
            e = [u, v, t[0]]
            if t[1] is not None:
                if t[0] != t[1]:
                    for s in range(t[0], t[1] + 1):
                        e = [u, v, s]
                        yield delimiter.join(map(make_str, e))
                else:
                    yield delimiter.join(map(make_str, e))
            else:
                yield delimiter.join(map(make_str, e))


@open_file(1, mode='wb')
def write_snapshots(G, path, delimiter=' ', encoding='utf-8'):
    """Write a DyNetx graph in snapshot graph list format.


        Parameters
        ----------

        G : graph
            A DyNetx graph.

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter

        encoding: str
            Encoding string, default utf-8
        """
    for line in generate_snapshots(G, delimiter):
        line += '\n'
        path.write(line.encode(encoding))


def parse_snapshots(lines, comments='#', directed=False, delimiter=None, nodetype=None, timestamptype=None, keys=None):
    if not directed:
        G = DynGraph()
    else:
        G = DynDiGraph()

    for line in lines:
        p = line.find(comments)
        if p >= 0:
            line = line[:p]
        if not len(line):
            continue
        # split line, should have 2 or more
        s = line.strip().split(delimiter)
        if len(s) < 3:
            continue
        if len(s) == 3:
            u = s.pop(0)
            v = s.pop(0)
            t = s.pop(0)
            e = None
        else:
            u = s.pop(0)
            v = s.pop(0)
            t = s.pop(0)
            e = s.pop(0)

        if nodetype is not None:
            try:
                u = nodetype(u)
                v = nodetype(v)
            except:
                raise TypeError("Failed to convert nodes %s,%s to type %s." % (u, v, nodetype))

        if timestamptype is not None:
            try:
                t = timestamptype(t)
                if e is not None:
                    e = timestamptype(e)
            except:
                raise TypeError("Failed to convert timestamp %s to type %s." % (t, nodetype))

        if keys is not None:
            t = keys[t]
            if e is not None:
                e = keys[e]
        G.add_interaction(u, v, t=t, e=e)
    return G


@open_file(0, mode='rb')
def read_snapshots(path, comments="#", directed=False, delimiter=None,
                   nodetype=None, timestamptype=None, encoding='utf-8', keys=False):
    """Read a DyNetx graph from snapshot graph list format.


        Parameters
        ----------

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter

        comments: character
            Comments row identifier

        directed: bool
            Whether the graph is directed or not

        nodetype: object
            node type

        timestamptype: object
            timestamp type

        encoding: str
            File encoding, default utf-8

        keys: bool
    """
    ids = None
    lines = (line.decode(encoding) for line in path)
    if keys:
        ids = read_ids(path.name, delimiter=delimiter, timestamptype=timestamptype)

    return parse_snapshots(lines, comments=comments, directed=directed, delimiter=delimiter, nodetype=nodetype,
                           timestamptype=timestamptype, keys=ids)


def read_ids(path, delimiter=None, timestamptype=None):
    f = open(path)
    ids = {}
    for line in f:
        s = line.rstrip().split(delimiter)
        ids[timestamptype(s[-1])] = None
        if len(line) == 4:
            if s[-2] not in ['+', '-']:
                ids[timestamptype(s[-2])] = None

    f.flush()
    f.close()

    ids = compact_timeslot(ids.keys())
    return ids
