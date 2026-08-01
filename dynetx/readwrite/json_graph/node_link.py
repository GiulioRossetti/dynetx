from dynetx.utils import make_str
import dynetx as dn
from itertools import chain, count

__all__ = ['node_link_data', 'node_link_graph']
_attrs = dict(id='id', source='source', target='target')


def node_link_data(G, attrs=_attrs):
    """Return data in node-link format that is suitable for JSON serialization
    and use in Javascript documents.

    Parameters
    ----------
    G : DyNetx graph

    attrs : dict
        A dictionary that contains three keys 'id', 'source' and 'target'.
        The corresponding values provide the attribute names for storing DyNetx-internal graph data. The values should be unique.
        Default value :samp:`dict(id='id', source='source', target='target')`.

    Returns
    -------
    data : dict
       A dictionary with node-link formatted data.

    Examples
    --------
    >>> from dynetx.readwrite import json_graph
    >>> import dynetx as dn
    >>> G = dn.DynGraph([(1,2)])
    >>> data = json_graph.node_link_data(G)

    To serialize with json

    >>> import json
    >>> s = json.dumps(data)

    Notes
    -----
    Graph, node, and link attributes are stored in this format. Note that
    attribute keys will be converted to strings in order to comply with
    JSON.

    See Also
    --------
    node_link_graph

    """
    id_ = attrs['id']

    data = {
        'schema': 'dynetx-temporal',
        'schema_version': 1,
        'directed': G.is_directed(),
        'graph': G.graph,
        'nodes': [dict(chain(G._node[n].items(), [(id_, n)])) for n in G],
        'links': [],
    }

    for u, v, timeline in G.interactions_iter():
        edge_attrs = {k: v_ for k, v_ in timeline.items() if k != 't'}
        for t in timeline['t']:
            link = {"source": u, "target": v, "t": t[0], "e": t[1]}
            link.update(edge_attrs)
            data['links'].append(link)

    return data


def node_link_graph(data, directed=False, attrs=_attrs):
    """Return graph from node-link data format.

    Parameters
    ----------
    data : dict
        node-link formatted graph data

    directed : bool
        If True, and direction not specified in data, return a directed graph.

    attrs : dict
        A dictionary that contains three keys 'id', 'source', 'target'.
        The corresponding values provide the attribute names for storing
        Dynetx-internal graph data. Default value:
        :samp:`dict(id='id', source='source', target='target')`.

    Returns
    -------
    G : DyNetx graph
       A DyNetx graph object

    Examples
    --------
    >>> from dynetx.readwrite import json_graph
    >>> import dynetx as dn
    >>> G = dn.DynGraph([(1,2)])
    >>> data = json_graph.node_link_data(G)
    >>> H = json_graph.node_link_graph(data)

    See Also
    --------
    node_link_data
    """

    directed = data.get('directed', directed)
    graph = dn.DynDiGraph() if directed else dn.DynGraph()

    id_ = attrs['id']
    graph.graph = data.get('graph', {})
    c = count()
    for d in data['nodes']:
        node = d.get(id_, next(c))
        nodedata = dict((make_str(k), v) for k, v in d.items() if k != id_)
        graph.add_node(node, **nodedata)
    for d in data['links']:
        attrs = dict((make_str(k), v) for k, v in d.items() if k not in {'source', 'target', 't', 'e', 'time'})
        if 't' in d:
            e = d.get('e')
            graph.add_interaction(d['source'], d["target"], d['t'], e=(None if e is None else e + 1), **attrs)
        else:
            graph.add_interaction(d['source'], d["target"], d['time'], **attrs)

    return graph
