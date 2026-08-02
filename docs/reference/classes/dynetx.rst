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
    DynGraph.update_node_attr
    DynGraph.update_node_attr_from


Dynamic Representation: Access Snapshots and Interactions
---------------------------------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.stream_interactions
	DynGraph.time_slice
	DynGraph.temporal_snapshots_ids
	DynGraph.interactions_per_snapshots
	DynGraph.inter_event_time_distribution
	DynGraph.temporal_degree
	DynGraph.avg_temporal_degree
	DynGraph.has_node_in_range
	DynGraph.has_interaction_in_range
	DynGraph.neighbors_in_range
	DynGraph.interactions_in_range
	DynGraph.window_slices
	DynGraph.to_networkx_graph


Stream Graph Measures and Algorithms
------------------------------------

.. autosummary::
	:toctree: generated/

	DynGraph.link_count
	DynGraph.node_duration
	DynGraph.link_duration
	DynGraph.compactness
	DynGraph.stream_degree
	DynGraph.expected_stream_degree
	DynGraph.stream_node_density
	DynGraph.stream_degree_density
	DynGraph.stream_neighborhood
	DynGraph.stream_neighborhood_density
	DynGraph.cluster_internal_neighborhood
	DynGraph.cluster_external_neighborhood
	DynGraph.cluster_internal_degree
	DynGraph.cluster_external_degree
	DynGraph.cluster_average_internal_degree
	DynGraph.cluster_average_external_degree
	DynGraph.stream_clustering_coefficient
	DynGraph.average_stream_clustering_coefficient
	DynGraph.stream_transitivity
	DynGraph.time_clustering_coefficient
	DynGraph.stream_clustering_coefficient_global
	DynGraph.stream_diameter
	DynGraph.stream_lapse
	DynGraph.stream_flood_time
	DynGraph.stream_time_to_reach
	DynGraph.constrained_time_respecting_paths
	DynGraph.stream_weakly_connected_components
	DynGraph.stream_strongly_connected_components
	DynGraph.reachability_stream_graph
	DynGraph.intra_cluster_density
	DynGraph.inter_cluster_density
	DynGraph.cluster_external_density
	DynGraph.quotient_stream
	DynGraph.line_stream
	DynGraph.stream_k_core
	DynGraph.stream_path_tree
	DynGraph.stream_cascade
	DynGraph.stream_closeness_centrality
	DynGraph.stream_betweenness_centrality
	DynGraph.stream_node_betweenness_centrality
	DynGraph.stream_time_betweenness_centrality
	DynGraph.delta_substream
	DynGraph.delta_density
	DynGraph.delta_degree
