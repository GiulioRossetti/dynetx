# `dynetx.generation`

This package contains the synthetic dynamic graph generators used by DyNetx.

## Layout

Each generator lives in its own module:

- `activity_driven.py`
- `activity_driven_memory.py`
- `event_shuffling.py`
- `timeline_shuffling.py`
- `link_shuffling.py`
- `inter_event_shuffling.py`
- `degree_constrained_link_shuffling.py`

Shared utilities used by multiple generators live in `_shared.py`.
The model registry and aliases are in `registry.py`.
The public dispatcher is in `synthetic.py`.

## Public API

The package root re-exports the generator functions for convenience:

- `generate_activity_driven_graph`
- `generate_activity_driven_memory_graph`
- `generate_event_shuffling_graph`
- `generate_timeline_shuffling_graph`
- `generate_link_shuffling_graph`
- `generate_inter_event_shuffling_graph`
- `generate_degree_constrained_link_shuffling_graph`
- `generate_synthetic_graph`

The compatibility wrapper `temporal_reference_models.py` is kept so existing
imports continue to work while the implementation remains split across dedicated
files.

