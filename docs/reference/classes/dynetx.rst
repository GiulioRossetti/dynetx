*************************
Undirected Dynamic Graphs
*************************

Overview
--------

.. currentmodule:: dynetx
.. autoclass:: DynGraph

Adding and removing nodes and edges
-----------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.__init__
	DynGraph.add_edge
	DynGraph.add_edges_from
	DynGraph.remove_edge
	DynGraph.remove_edges_from
	DynGraph.add_star
	DynGraph.add_path
	DynGraph.add_cycle


Iterating over nodes and edges
------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.edges
	DynGraph.edges_iter
	DynGraph.neighbors
	DynGraph.neighbors_iter
	DynGraph.nodes
	DynGraph.nodes_iter

Information about graph structure
---------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.has_edge
	DynGraph.number_of_edges
	DynGraph.degree
	DynGraph.degree_iter
	DynGraph.size
	DynGraph.order
	DynGraph.has_node
	DynGraph.number_of_nodes


Dynamic Representation: Access Snapshots and Iterations
-------------------------------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.stream_edges
	DynGraph.time_slice
	DynGraph.temporal_snapshots
	DynGraph.number_of_interactions