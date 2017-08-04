*********
Functions
*********

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


Edges
-----
.. autosummary::
   :toctree: generated/


   edges
   number_of_edges
   non_edges


Attributes
----------
.. autosummary::
   :toctree: generated/

   set_node_attributes
   get_node_attributes
   set_edge_attributes
   get_edge_attributes


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

	time_slice
	stream_edges
