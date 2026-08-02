**********
Generation
**********

The ``dynetx.generation`` submodule hosts the synthetic dynamic graph
generators used by DyNetx.

The package is organized so that each generator lives in its own dedicated
module, while the package root re-exports the public API for convenience.

Package layout
==============

.. toctree::
   :maxdepth: 1

   temporal_reference_models

Public generators
=================

.. automodule:: dynetx.generation
.. autosummary::
   :toctree: generated/

   generate_activity_driven_graph
   generate_activity_driven_memory_graph
   generate_event_shuffling_graph
   generate_timeline_shuffling_graph
   generate_link_shuffling_graph
   generate_inter_event_shuffling_graph
   generate_degree_constrained_link_shuffling_graph
   generate_synthetic_graph

Model modules
=============

The following modules contain the implementation for the public generators:

- ``activity_driven.py``
- ``activity_driven_memory.py``
- ``event_shuffling.py``
- ``timeline_shuffling.py``
- ``link_shuffling.py``
- ``inter_event_shuffling.py``
- ``degree_constrained_link_shuffling.py``
- ``synthetic.py``
- ``registry.py``
- ``_shared.py``

The compatibility wrapper ``temporal_reference_models.py`` remains available so
older imports keep working while the implementation is split across dedicated
files.

