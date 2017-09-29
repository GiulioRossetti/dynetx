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
	DynGraph.add_interaction
	DynGraph.add_interactions_from
	DynGraph.add_star
	DynGraph.add_path
	DynGraph.add_cycle


Iterating over nodes and edges
------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.interactions
	DynGraph.interactions_iter
	DynGraph.neighbors
	DynGraph.neighbors_iter
	DynGraph.nodes
	DynGraph.nodes_iter

Information about graph structure
---------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.has_interaction
	DynGraph.number_of_interactions
	DynGraph.degree
	DynGraph.degree_iter
	DynGraph.size
	DynGraph.order
	DynGraph.has_node
	DynGraph.number_of_nodes
	DynGraph.to_directed


Dynamic Representation: Access Snapshots and Interactions
---------------------------------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.stream_interactions
	DynGraph.time_slice
	DynGraph.temporal_snapshots_ids
	DynGraph.interactions_per_snapshots
	DynGraph.inter_event_time_distribution