*********
Functions
*********

Functional interface to graph methods and assorted utilities.

.. automodule:: dynetx.classes.function

Graph
-----
.. autosummary::
   :toctree: generated/

   degree
   degree_histogram
   density
   create_empty_copy
   is_directed
   add_star
   add_path
   add_cycle


Nodes
-----
.. autosummary::
   :toctree: generated/

   nodes
   number_of_nodes
   all_neighbors
   non_neighbors


Interactions
------------
.. autosummary::
   :toctree: generated/


   interactions
   number_of_interactions
   non_interactions


Freezing graph structure
------------------------
.. autosummary::
   :toctree: generated/

   freeze
   is_frozen

Snapshots and Interaction Stream
--------------------------------
.. autosummary::
   :toctree: generated/

	stream_interactions
	time_slice
	temporal_snapshots_ids
	interactions_per_snapshots
	inter_event_time_distribution
