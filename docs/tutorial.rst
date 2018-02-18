***************
DyNetx Tutorial
***************

DyNetx is built upon networkx and is designed to configure, model and analyze dynamic networks.

In this tutorial we will introduce the ``DynGraph`` object that can be used to describe undirected, temporal graphs.

Creating a graph
----------------

Create an empty dynamic graph with no nodes and no edges.

.. code:: python

	import dynetx as dn
	g = dn.DynGraph(edge_removal=True)

During the construction phase the ``edge_removal`` parameter allows to specify if the dynamic graph will allow edge removal or not.

^^^^^^^^^^^^
Interactions
^^^^^^^^^^^^

``G`` can  be grown by adding one interaction at a time.
Every interaction is univocally defined by its endpoints, ``u`` and ``v``, as well as its timestamp ``t``.

.. code:: python

	g.add_interaction(u=1, v=2, t=0)

Moreover, also interaction duration can be specified at creation time:

.. code:: python

	g.add_interaction(u=1, v=2, t=0, e=3)

In the above example the interaction ``(1, 2)`` appear at time ``0`` and vanish at time ``3``, thus being present in ``[0, 2]``.

Interaction list can also be added: in such scenario all the interactions in the list will have a same timestamp (i.e. they will belong to a same network *snapshot*)

.. code:: python

	g.add_interactions_from([(1, 2), (2, 3), (3, 1)], t=2)

The same method can be used to add any ``ebunch`` of interaction.  An *ebunch* is any iterable container of interaction-tuples.

.. code:: python

	g.add_interactions_from(H.edges(), t=2)


^^^^^
Nodes
^^^^^

Flattened node degree can be computed via the usual ``degree`` method exposed by ``networkx`` graph objects.
In order to get the time dependent degree a parameter ``t``, identifying the desired snapshot, must be specified.

Similarly, the ``neighbors`` method has been extended with a similar optional filtering parameter ``t``.

Read graph from file
--------------------

``DyNetx`` allows to read/write networks from files in two formats:

 - snapshot graph (extended edgelist)
 - interaction graph (extended edgelist)

The former format describes the dynamic graph one edge per row as a 3-tuple

.. code:: bash

	n1 n2 t1

where

 - ``n1`` and ``n2`` are nodes
 - ``t1`` is the timestamp of interaction appearance

The latter format describes the dynamic graph one interaction per row as a 4-tuple

.. code:: bash

	n1 n2 op t1

where

 - ``n1`` and ``n2`` are nodes
 - ``t1`` is the timestamp of interaction appearance
 - ``op`` identify either the insertion, ``+``, or deletion, ``-`` of the edge

^^^^^^^^^^^^^^
Snapshot Graph
^^^^^^^^^^^^^^

In order to read a snapshot graph file

.. code:: python

	g = dn.read_snapshots(graph_filename, nodetype=int, timestamptype=int)

in order to save a graph in the same format

.. code:: python

	dn.write_snapshots(graph, graph_filename)


^^^^^^^^^^^^^^^^^
Interaction Graph
^^^^^^^^^^^^^^^^^

In order to read an interaction graph file


.. code:: python

	g = dn.read_interactions(graph_filename, nodetype=int, timestamptype=int)

in order to save a graph in the same format

.. code:: python

	dn.write_interactions(graph, graph_filename)


Snapshots and Interactions
--------------------------

The timestamps associated to graph edges can be retrieved through

.. code:: python

	g.temporal_snapshots_ids()

Similarly, the number of interactions in a given snapshot can be obtained via

.. code:: python

	g.number_of_interactions(t=snapshot_id)

if the parameter ``t`` is not specified a dictionary snapshot->edges number will be returned.


Slicing a Dynamic Network
-------------------------

Once loaded a graph it is possible to extract from it a time slice, i.e., a time-span graph

.. code:: python

	s = g.time_slice(t_from=2, t_to=3)

the resulting ``DynGraph`` stored in ``s`` will be composed by nodes and interactions existing within the time span ``[2, 3]``.


Obtain the Interaction Stream
-----------------------------

A dynamic network can be also described as stream of interactions, a chronologically ordered list of interactions

.. code:: python

	for e in g.stream_interactions():
		print e

the ``stream_interactions`` method returns a generator that streams the interactions in ``g``, where ``e`` is a 4-tuple ``(u, v, op, t)``

 - ``u, v`` are nodes
 - ``op`` is a edge creation or deletion event (respectively ``+``, ``-``)
 - ``t`` is the interactions timestamp

