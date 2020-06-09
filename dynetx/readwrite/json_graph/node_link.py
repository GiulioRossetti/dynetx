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

    data = {'directed': G.is_directed(), 'graph': G.graph,
            'nodes': [dict(chain(G._node[n].items(), [(id_, n)])) for n in G], 'links': []}

    for u, v, timeline in G.interactions_iter():
        for t in timeline['t']:
            for tid in range(t[0], t[-1]+1):
                data['links'].append({"source": u, "target": v, "time": tid})

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
    graph = dn.DynGraph()
    if directed:
        graph = graph.to_directed()

    id_ = attrs['id']
    mapping = []
    graph.graph = data.get('graph', {})
    c = count()
    for d in data['nodes']:
        node = d.get(id_, next(c))
        mapping.append(node)
        nodedata = dict((make_str(k), v) for k, v in d.items() if k != id_)
        graph.add_node(node, **nodedata)
    for d in data['links']:
        graph.add_interaction(d['source'], d["target"], d['time'])

    return graph
