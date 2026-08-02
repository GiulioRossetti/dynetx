# Temporal Reference Models

This note documents the temporal reference-model generators implemented in
`dynetx.generation` and surfaced in the dashboard.

The implementation target is the family of randomized reference models surveyed in:

- Laetitia Gauvin, Mathieu Génois, Márton Karsai, Mikko Kivelä, Taro Takaguchi,
  Eugenio Valdano, and Christian L. Vestergaard, *Randomized reference models for
  temporal networks*, SIAM Review 64(4), 763-830, 2022.

The generators are intended to work with DyNetx temporal graphs and return either:

- a **stream graph** (`DynGraph` with interval-valued interactions), or
- a **snapshot graph** (`DynGraph` interpreted snapshot-by-snapshot),

depending on the selected model.

## Design goals

- Keep the API in a dedicated `dynetx.generation` submodule.
- Preserve the selected invariant explicitly in the generator name.
- Make each model usable both from the library API and from the dashboard.
- Keep the implementation synthetic and self-contained so it can be used without
  an empirical input network.

## Models

### 1. Event shuffling

**Canonical name:** `event_shuffling`

**Output type:** stream graph

**Idea:** Randomly permute event timestamps across the event multiset while
preserving:

- the node set,
- the number of events,
- the static projection of interacting node pairs,
- the global time span.

**Effect:** destroys the original time ordering while keeping which nodes
interact and how often.

**Paper connection:** this is one of the core event-level randomized reference
models discussed by Gauvin et al.

### 2. Timeline shuffling

**Canonical name:** `timeline_shuffling`

**Output type:** stream graph

**Idea:** Treat each edge as a full interaction timeline and randomly assign
whole timelines to other edges.

**Preserved:**

- static topology,
- per-edge timeline length,
- event counts per edge.

**Randomized:**

- which edge receives which timeline,
- temporal correlations between topology and timelines.

**Paper connection:** this matches the timeline-shuffling family discussed in
the SIAM Review paper.

### 3. Link shuffling

**Canonical name:** `link_shuffling`

**Output type:** stream graph

**Idea:** Randomly reassign event timelines to links while preserving the
distribution of link timelines.

**Preserved:**

- the multiset of timelines,
- the number of links,
- the time span.

**Randomized:**

- the pairing between timelines and node pairs.

**Paper connection:** this is the broader link-level shuffling family used in
the paper’s taxonomy.

### 4. Inter-event shuffling

**Canonical name:** `inter_event_shuffling`

**Output type:** stream graph

**Idea:** For each link, preserve the first and last event but shuffle the
inter-event gaps on that link.

**Preserved:**

- edge identities,
- number of events per edge,
- first and last event time on each edge.

**Randomized:**

- the spacing between consecutive events on the same edge.

**Paper connection:** this is a standard temporal null model for preserving
local edge activity while destroying burst patterns.

### 5. Degree-constrained link shuffling

**Canonical name:** `degree_constrained_link_shuffling`

**Output type:** snapshot graph

**Idea:** Randomize the static edges using a degree-preserving rewiring model
and then assign those randomized snapshots across the time axis.

**Preserved:**

- degree sequence of the static projection,
- snapshot count,
- time range.

**Randomized:**

- the concrete edge identities,
- temporal alignment with the original topology.

**Paper connection:** this is the degree-constrained link shuffling family
discussed in the paper’s taxonomy of link-based MRRMs.

## Public API

The generators are exposed as:

```python
import dynetx as dn

G1 = dn.generation.generate_event_shuffling_graph(...)
G2 = dn.generation.generate_timeline_shuffling_graph(...)
G3 = dn.generation.generate_link_shuffling_graph(...)
G4 = dn.generation.generate_inter_event_shuffling_graph(...)
G5 = dn.generation.generate_degree_constrained_link_shuffling_graph(...)
```

For convenience, the same functions are also re-exported at the package root to
preserve the current `dynetx` import style.

## Implementation notes

- The generators use DyNetx `DynGraph` objects.
- Stream models use interval-valued interactions with `t` and `e`.
- Snapshot models are assembled as consecutive snapshot interactions.
- The dashboard surfaces the models under the synthetic generator panel and
  automatically switches the graph kind when a model only supports stream or
  snapshot output.

## References

- Gauvin, L., Génois, M., Karsai, M., Kivelä, M., Takaguchi, T., Valdano, E.,
  and Vestergaard, C. L. *Randomized reference models for temporal networks*.
  SIAM Review 64(4), 763-830 (2022).
- Perra, N., Gonçalves, B., Pastor-Satorras, R., and Vespignani, A. *Activity
  driven modeling of time varying networks*. Scientific Reports 2 (2012).
- Karsai, M., Perra, N., and Vespignani, A. *Time varying networks and the
  weakness of strong ties*. Scientific Reports 4, 4001 (2014).
