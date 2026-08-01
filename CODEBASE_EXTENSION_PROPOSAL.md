# DyNetx Extension Proposal

This document proposes the next set of features and structural improvements that would make DyNetx more usable, more adaptable to real workloads, and easier to integrate into modern data pipelines.

The recommendations are ordered by practical relevance:

1. Improve the basic API surface so common graph workflows feel complete.
2. Fill in missing temporal primitives that users expect from a dynamic network library.
3. Expand interoperability with the broader Python data ecosystem.
4. Add scale and ergonomics features that reduce friction in production use.

## Current Gaps That Limit Usability

The codebase already covers core dynamic graph construction, snapshots, path analysis, and a small set of read/write formats. The main limitations are:

- Several compatibility methods are still intentionally unimplemented in the graph classes, especially around removal, edge-level mutation, and edge attribute APIs in [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1478) and [`dynetx/classes/dyndigraph.py`](dynetx/classes/dyndigraph.py#L1677).
- Temporal analytics are still narrow: there is no first-class temporal centrality, temporal clustering, reachability filtering, or window abstraction beyond `time_slice()` and the path/conformity helpers in [`dynetx/classes/function.py`](dynetx/classes/function.py#L683).
- Read/write support is limited to edge-list and a custom node-link shape in [`dynetx/readwrite/edgelist.py`](dynetx/readwrite/edgelist.py#L1) and [`dynetx/readwrite/json_graph/node_link.py`](dynetx/readwrite/json_graph/node_link.py#L1).
- The package does not yet provide strong typing, formal error contracts, or ecosystem adapters for tabular data, which makes it harder to adopt in larger projects.

## Proposed Extensions

### 1. Complete the Core Graph API

This is the highest-value improvement because it closes the gap between DyNetx and the expectations users already have from NetworkX-like objects.

Add:

- Real removal semantics for nodes and edges, including temporal removal windows.
- Edge attribute APIs for setting, reading, and querying temporal edge metadata.
- A supported `temporal_degree()` and `avg_temporal_degree()` implementation, which are currently placeholders in [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1470).
- Consistent iterator/list variants for nodes, interactions, predecessors, successors, and time-filtered views.
- A stable copy/deepcopy contract for graph slices and conversions.

Why this matters:

- Users can keep a single mental model for graph mutation instead of memorizing which methods are intentionally missing.
- It lowers the risk of adopting DyNetx as a drop-in temporal graph backend.

### 2. Add First-Class Temporal Query Primitives

DyNetx should make temporal querying feel native rather than assembled from low-level helpers.

Add:

- Attribute-filtered time slicing, e.g. slice by node labels, edge labels, or interaction metadata.
- Temporal neighborhood queries with interval predicates, not just a single timestamp.
- Faster “present at any time in range” and “present at all times in range” predicates.
- API-level support for event windows, sliding windows, and tumbling windows.
- Declarative query helpers for common questions:
  - “Who interacted with node X in the last N snapshots?”
  - “Which nodes were active in every snapshot of a window?”
  - “Which edges appeared at least K times in a range?”

Why this matters:

- Most temporal-network users think in windows and intervals, not just exact timestamps.
- These primitives are the building blocks for dashboards, analyses, and downstream models.

### 3. Expand Temporal Analytics

The current algorithms module is useful but small. The next step should be a broader analytics toolkit.

Add:

- Temporal centrality measures:
  - temporal degree centrality
  - reachability-aware betweenness
  - earliest-arrival closeness
- Temporal clustering and triadic closure metrics.
- Inter-event statistics beyond the current distribution helpers.
- Component and connectivity analysis over time.
- Path summaries that expose:
  - earliest path
  - fastest path
  - most persistent path
  - path stability across windows

Why this matters:

- It moves DyNetx from “data structure + a few algorithms” toward a usable temporal analysis library.
- It gives users a meaningful answer to “what should I compute next?” without leaving the package.

### 4. Improve Interoperability and I/O

This should be treated as product infrastructure, not as a secondary convenience feature.

Add:

- Import/export for common graph interchange formats:
  - GraphML where feasible
  - GEXF or a documented equivalent temporal JSON schema
  - CSV/TSV with explicit schema headers
- Tabular adapters:
  - pandas DataFrame in/out
  - optional Arrow/Parquet pathways for large datasets
- A well-specified temporal JSON schema with versioning.
- Safer round-trip handling for intervals, keys, labels, and directedness.
- Better filename/path support using `pathlib.Path` and file-like objects uniformly.

Why this matters:

- Users need to move data in and out of the library without writing custom parsing code.
- Strong I/O makes the package easier to embed in ETL and notebook workflows.

### 5. Make the Library Adaptable to Larger Workflows

This is about making DyNetx survive beyond notebook-scale examples.

Add:

- Optional lazy or streaming builders for large event logs.
- Batch ingestion APIs for append-only streams.
- Memory-aware representation choices:
  - interval compression
  - sparse adjacency storage
  - configurable snapshot indexing
- Optional parallelism for expensive analytics jobs.
- Hooks or callbacks for integrating with monitoring and ETL pipelines.

Why this matters:

- Temporal networks get large quickly.
- Users need a path from toy examples to tens of millions of events without rewriting their pipeline.

### 6. Improve Developer Experience and Reliability

These features do not add new domain capability, but they make adoption materially easier.

Add:

- Type hints across the public API.
- Consistent exception classes and validation errors.
- Better docstrings with parameter semantics, edge cases, and examples.
- A more explicit “supported / not supported” contract in the docs.
- A deprecation policy for any legacy aliases or ambiguous behaviors.

Why this matters:

- The codebase already has a number of compatibility edges and internal conventions.
- Clear contracts reduce support burden and user confusion.

## Phased Integration Pipeline

### Phase 1: Baseline Completeness

Goal: make the object model feel finished and predictable.

Deliverables:

1. Implement node/edge removal semantics or explicitly expose temporal deletion as a supported operation.
2. Add edge attribute setters/getters and formalize their storage model.
3. Implement `temporal_degree()` and `avg_temporal_degree()`.
4. Normalize iterators and list-returning helpers so their behavior is consistent across directed and undirected graphs.
5. Add regression tests for mutation, copy, and slice behavior.

Why first:

- This is the minimum required for DyNetx to feel like a usable graph library rather than a partially implemented research prototype.

### Phase 2: Temporal Query Power

Goal: make common temporal queries easy to express.

Deliverables:

1. Window-aware filters and predicates.
2. Attribute-aware slicing and neighborhood queries.
3. A small query helper layer for common time-range questions.
4. Stable helper functions for “active at time,” “active in range,” and “active for entire range.”

Why second:

- These features are the most immediately useful for analysts working with real dynamic data.

### Phase 3: Analytics Expansion

Goal: broaden the analytical value of the package.

Deliverables:

1. Temporal centrality primitives.
2. Temporal clustering and persistence metrics.
3. Connectivity and component tracking over time.
4. Richer path summaries and reachability statistics.

Why third:

- Once querying is pleasant, users will immediately want higher-level metrics to operate on the same data model.

### Phase 4: I/O and Ecosystem Integration

Goal: make DyNetx easy to plug into existing workflows.

Deliverables:

1. A versioned temporal JSON schema.
2. DataFrame import/export helpers.
3. Optional Parquet/Arrow/CSV pathways.
4. Better round-trip guarantees for intervals, directedness, and metadata.

Why fourth:

- These features improve adoption and reduce integration work, but they are most effective once the internal model is stable.

### Phase 5: Scale and Adaptability

Goal: make DyNetx suitable for larger and longer-running workloads.

Deliverables:

1. Streaming ingestion APIs.
2. Memory-optimized storage options.
3. Optional batch/parallel execution for expensive analytics.
4. Progress reporting and instrumentation hooks.

Why fifth:

- Performance work should build on a stable API and a clear semantic model.

### Phase 6: Polish and Governance

Goal: reduce friction for contributors and downstream users.

Deliverables:

1. Type hints for public APIs.
2. Stronger exception taxonomy.
3. Expanded documentation and worked examples.
4. A deprecation and compatibility policy.

Why last:

- These changes are high leverage, but they are most effective after the core capabilities are in place.

## Priority Order Summary

If the goal is maximum usability per unit of implementation effort, the recommended order is:

1. Complete the core graph API.
2. Add temporal query primitives.
3. Expand analytics.
4. Improve interoperability and I/O.
5. Add scale/adaptability features.
6. Polish typing, exceptions, and docs.

## Suggested MVP Expansion Set

If only a small tranche of work is feasible, the best near-term package would be:

- Edge attribute support.
- Mutation/removal semantics.
- Window-aware slicing and predicates.
- Temporal centrality and clustering basics.
- DataFrame import/export.

That subset would materially improve usability without forcing a redesign of the current architecture.

