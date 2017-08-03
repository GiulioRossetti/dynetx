**************
DyNet Tutorial
**************

DyNet is built upon networkx and is designed to configure, model and analyze dynamic networks.

------------------------
Creating a Dynamic Graph
------------------------

..  -*- coding: utf-8 -*-

Tutorial
========

Start here to begin working with DyNet.

Creating a graph
----------------

Create an empty dynamic graph with no nodes and no edges.

.. code:: python

	import dynet as dt
	g = dt.DynGraph()




Edges
-----

``G`` can  be grown by adding one edge at a time.
Every edge is univocally defined by its endpoints, ``u`` and ``v``, as well as its timestamp ``t``.

.. code:: python

	g.add_edge(u=1, v=2, t=0)

Moreover, also edge duration can be specified at creation time:

.. code:: python

	g.add_edge(u=1, v=2, t=0, e=3)

In the above example the edge ``(1, 2)`` appear at time ``0`` and vanish at time ``3``, thus being present in ``[0, 2]``.

Edges list can also be added: in such scenario all the edges in the list will have a same timestamp (i.e. they will belong to a same network *snapshot*)

.. code:: python

	g.add_edges_from([(1, 2), (2, 3), (3, 1)], t=2)

The same method can be used to add any ``ebunch`` of edges.  An *ebunch* is any iterable container of edge-tuples.

.. code:: python

	g.add_edges_from(H.edges(), t=2)


Accessing edges
---------------

