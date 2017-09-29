***********************
Directed Dynamic Graphs
***********************

Overview
--------

.. currentmodule:: dynetx
.. autoclass:: DynDiGraph

Adding and removing nodes and edges
-----------------------------------

.. autosummary::
	:toctree: generated/

	DynDiGraph.__init__
	DynDiGraph.add_interaction
	DynDiGraph.add_interactions_from


Iterating over nodes and edges
------------------------------

.. autosummary::
	:toctree: generated/

	DynDiGraph.interactions
	DynDiGraph.interactions_iter
	DynDiGraph.in_interactions
	DynDiGraph.in_interactions_iter
	DynDiGraph.out_interactions
	DynDiGraph.out_interactions_iter
	DynDiGraph.neighbors
	DynDiGraph.neighbors_iter
	DynDiGraph.successors
	DynDiGraph.successors_iter
	DynDiGraph.predecessors
	DynDiGraph.predecessors_iter
	DynDiGraph.nodes
	DynDiGraph.nodes_iter

Information about graph structure
---------------------------------

.. autosummary::
	:toctree: generated/

	DynDiGraph.has_interaction
	DynDiGraph.has_successor
	DynDiGraph.has_predecessor
	DynDiGraph.number_of_interactions
	DynDiGraph.degree
	DynDiGraph.degree_iter
	DynDiGraph.in_degree
	DynDiGraph.in_degree_iter
	DynDiGraph.out_degree
	DynDiGraph.out_degree_iter
	DynDiGraph.size
	DynDiGraph.order
	DynDiGraph.has_node
	DynDiGraph.number_of_nodes
	DynGraph.to_undirected


Dynamic Representation: Access Snapshots and Interactions
---------------------------------------------------------

.. autosummary::
	:toctree: generated/

	DynDiGraph.stream_interactions
	DynDiGraph.time_slice
	DynDiGraph.temporal_snapshots_ids
	DynDiGraph.interactions_per_snapshots
	DynDiGraph.inter_event_time_distribution
	DynDiGraph.inter_in_event_time_distribution
	DynDiGraph.inter_out_event_time_distribution