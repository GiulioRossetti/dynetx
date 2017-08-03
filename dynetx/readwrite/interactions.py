from networkx.utils import open_file, make_str
from dynetx.classes.dyngraph import DynGraph

__author__ = 'Giulio Rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

__all__ = ['write_interactions',
           'generate_interactions',
           'parse_interactions',
           'read_interactions',
           'generate_sn_edgelist',
           'write_sn_edgelist',
           'parse_sn_edgelist',
           'read_sn_edgelist']


def generate_interactions(G, delimiter=' '):
    for e in G.stream_edges():
        yield delimiter.join(map(make_str, e))


@open_file(1, mode='wb')
def write_interactions(G, path, delimiter=' ',  encoding='utf-8'):

    for line in generate_interactions(G, delimiter):
        line += '\n'
        path.write(line.encode(encoding))


@open_file(0, mode='rb')
def read_interactions(path, comments="#", delimiter=None, create_using=None,
                  nodetype=None, timestamptype=None, encoding='utf-8'):

    lines = (line.decode(encoding) for line in path)
    return parse_interactions(lines, comments=comments, delimiter=delimiter, create_using=create_using, nodetype=nodetype,
                             timestamptype=timestamptype)


def parse_interactions(lines, comments='#', delimiter=None, create_using=None, nodetype=None, timestamptype=None):
    if create_using is None:
        G = DynGraph()
    else:
        try:
            G = create_using
            G.clear()
        except:
            raise TypeError("create_using input is not a DyNet graph type")

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
        if op == '+':
            G.add_edge(u, v, t=s)
        else:
            timestamps = G.edge[u][v]['t']
            if len(timestamps) > 0 and timestamps[-1] < s:
                for t in range(timestamps[-1], s):
                    G.add_edge(u, v, t=t)
    return G


def generate_sn_edgelist(G, delimiter=' '):

    for u, v, d in G.edges(data=True):
        if 't' not in d:
            raise NotImplemented
        for t in d['t']:
            e = [u, v, t]

            try:
                e.extend(d[k] for k in d if k != "t")
            except KeyError:
                pass
            yield delimiter.join(map(make_str, e))


@open_file(1, mode='wb')
def write_sn_edgelist(G, path, delimiter=' ',  encoding='utf-8'):

    for line in generate_sn_edgelist(G, delimiter):
        line += '\n'
        path.write(line.encode(encoding))


def parse_sn_edgelist(lines, comments='#', delimiter=None, create_using=None, nodetype=None, timestamptype=None):
    if create_using is None:
        G = DynGraph()
    else:
        try:
            G = create_using
            G.clear()
        except:
            raise TypeError("create_using input is not a DyNet graph type")

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
            except:
                raise TypeError("Failed to convert timestamp %s to type %s." % (t, nodetype))

        G.add_edge(u, v, t=t, e=e)
    return G


@open_file(0, mode='rb')
def read_sn_edgelist(path, comments="#", delimiter=None, create_using=None,
                  nodetype=None, timestamptype=None, encoding='utf-8'):

    lines = (line.decode(encoding) for line in path)
    return parse_sn_edgelist(lines, comments=comments, delimiter=delimiter, create_using=create_using, nodetype=nodetype,
                             timestamptype=timestamptype)
