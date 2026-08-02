***********************************
Temporal Reference Model Generators
***********************************

DyNetx provides synthetic generators inspired by the randomized reference
models surveyed by Gauvin *et al.* in *Randomized reference models for temporal
networks* (SIAM Review, 2022). The generators are exposed through
``dynetx.generation`` and re-exported by ``dynetx`` and ``dynetx.dashboard``.

The implementation is intentionally synthetic: when no empirical network is
available, the generators build a base temporal DyNetx graph and then apply the
chosen randomization principle.

Public API
==========

.. automodule:: dynetx.generation.temporal_reference_models
.. autosummary::
   :toctree: generated/

   generate_event_shuffling_graph
   generate_timeline_shuffling_graph
   generate_link_shuffling_graph
   generate_inter_event_shuffling_graph
   generate_degree_constrained_link_shuffling_graph

Stream-graph reference models
=============================

Event shuffling
---------------

``generate_event_shuffling_graph`` returns a stream graph where contact start
times are permuted across the event multiset while preserving the interacting
node pairs and contact durations. The result is suitable for removing temporal
ordering effects while keeping the static projection intact.

Timeline shuffling
-------------------

``generate_timeline_shuffling_graph`` permutes complete edge timelines across
the available links. The internal event structure of each timeline is
preserved, but the association between a timeline and a specific pair of nodes
is randomized.

Link shuffling
--------------

``generate_link_shuffling_graph`` rewires timelines onto fresh node pairs.
Compared with timeline shuffling, this variant changes the topology associated
with each temporal profile.

Inter-event shuffling
---------------------

``generate_inter_event_shuffling_graph`` keeps each link identity but shuffles
the gaps between consecutive events on that link. This preserves the number of
events per link while destroying burstiness patterns.

Snapshot-graph reference model
==============================

Degree-constrained link shuffling
---------------------------------

``generate_degree_constrained_link_shuffling_graph`` returns a snapshot-based
temporal graph where each snapshot is randomized under a degree-sequence
constraint. The model is useful when the degree distribution of the static
projection should be preserved while temporal alignment is randomized.

References
==========

- Gauvin, L., Génois, M., Karsai, M., Kivelä, M., Takaguchi, T., Valdano, E.,
  and Vestergaard, C. L. *Randomized reference models for temporal networks*.
  SIAM Review 64(4), 763-830 (2022).
- Perra, N., Gonçalves, B., Pastor-Satorras, R., and Vespignani, A.
  *Activity driven modeling of time varying networks*. Scientific Reports 2
  (2012).
- Karsai, M., Perra, N., and Vespignani, A. *Time varying networks and the
  weakness of strong ties*. Scientific Reports 4, 4001 (2014).
