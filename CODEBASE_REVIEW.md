# DyNetx Codebase Review

This review focuses on concrete bugs, behavioral errors, and internal inconsistencies in the current codebase. The repository test suite currently passes, so the issues below are mostly latent correctness problems, edge-case failures, and API mismatches that are not covered by the existing tests.

## Executive Summary

The most important problems are in the core graph API and the temporal analytics layer:

1. `get_node_snapshots()` returns the wrong value in both graph classes.
2. `interactions_per_snapshots()` is mathematically wrong for interval edges.
3. Several summary metrics crash on empty graphs or degenerate inputs.
4. `temporal_dag()` cannot safely handle valid string node IDs containing underscores.
5. `update_node_attr()` and `update_node_attr_from()` discard existing node attributes instead of merging.
6. Snapshot read/write key handling is brittle and partially broken.

These are not stylistic issues. They can corrupt outputs, drop results, or raise runtime exceptions in common workflows.

## Findings

### P0 - Core API returns the wrong value

**Files**
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1089)
- [`dynetx/classes/dyndigraph.py`](dynetx/classes/dyndigraph.py#L219)

**Problem**

`get_node_snapshots()` builds a `snaps` list but returns `t`, which is just the last loop variable. In practice this means the method returns a scalar snapshot id, not the list of snapshots requested by the docstring.

**Why it matters**

Any caller using this helper for temporal filtering, reporting, or downstream analytics will get the wrong type and wrong content.

**Repro**

```python
import dynetx as dn
G = dn.DynGraph()
G.add_interaction(1, 2, t=3)
G.get_node_snapshots(1)   # returns 3 instead of [3]
```

**Priority**

Fix immediately and add regression tests in both graph classes.

---

### P0 - Snapshot counts are wrong for interval edges

**Files**
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1142)
- [`dynetx/classes/dyndigraph.py`](dynetx/classes/dyndigraph.py#L1390)

**Problem**

`interactions_per_snapshots()` divides every stored count by `2`, regardless of how the snapshot counters were produced.

That happens to work for instantaneous edges because `add_interaction(u, v, t)` stores `t` twice as `[t, t]`, but it breaks interval edges added with `e=` because those are counted once per snapshot and then divided by two.

**Observed behavior**

```python
import dynetx as dn
G = dn.DynGraph()
G.add_interaction(1, 2, 1, 3)
G.interactions_per_snapshots()   # {1: 0.5, 2: 0.5}
```

**Why it matters**

This directly corrupts temporal statistics and any report or model built on per-snapshot interaction counts.

**Priority**

Critical. This is a core metric that should never emit fractional counts.

---

### P0 - Temporal analytics crash on empty or degenerate inputs

**Files**
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1254)
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1313)
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1341)

**Problem**

Several graph summary methods divide by zero when the graph has no snapshots or when the denominator collapses to zero:

- `coverage()`
- `node_contribution()`
- `node_pair_uniformity()`
- `uniformity()`
- `density()`

**Observed behavior**

```python
import dynetx as dn
G = dn.DynGraph()
G.coverage()     # ZeroDivisionError
G.uniformity()   # ZeroDivisionError
```

**Why it matters**

Empty graphs, partially constructed graphs, and narrow slices are normal states in temporal workflows. These helpers should return a neutral value or a documented exception, not crash.

**Priority**

High. Add guards and define explicit return semantics for empty graphs.

---

### P1 - Node attribute updates overwrite existing metadata

**Files**
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1087)
- [`dynetx/classes/dyngraph.py`](dynetx/classes/dyngraph.py#L1102)
- [`dynetx/classes/dyndigraph.py`](dynetx/classes/dyndigraph.py#L1360)

**Problem**

`update_node_attr()` and `update_node_attr_from()` assign `self._node[n] = data` instead of merging `data` into the existing node attribute dictionary.

That means this code:

```python
G.add_node(1, a=1)
G.update_node_attr(1, b=2)
```

ends up with `{"b": 2}` instead of `{"a": 1, "b": 2}`.

**Why it matters**

This silently drops metadata and diverges from the expected NetworkX-style attribute update behavior.

**Priority**

High. This is silent data loss.

---

### P1 - Temporal DAG generation breaks on valid node names containing underscores

**Files**
- [`dynetx/algorithms/paths.py`](dynetx/algorithms/paths.py#L17)
- [`dynetx/algorithms/paths.py`](dynetx/algorithms/paths.py#L95)
- [`dynetx/algorithms/paths.py`](dynetx/algorithms/paths.py#L182)

**Problem**

`temporal_dag()` encodes temporal occurrences as strings and later recovers the original node id with `str(an).split("_")[0]`.

That is unsafe because the library explicitly allows arbitrary hashable node IDs, including strings with underscores. A node like `"A_B"` is interpreted as `"A"` during neighbor lookup, which breaks traversal and can silently produce an empty DAG.

**Observed behavior**

```python
import dynetx as dn
from dynetx.algorithms.paths import temporal_dag

G = dn.DynGraph()
G.add_interaction("A_B", "C", 1)
G.add_interaction("C", "D", 2)
temporal_dag(G, "A_B", "D", start=1, end=2)
# returns no usable traversal for the A_B branch
```

**Why it matters**

This is a correctness bug for a perfectly valid node namespace. It is also hard to diagnose because it fails by omission rather than with an explicit error.

**Priority**

High. Replace string-splitting with an unambiguous temporal node encoding.

---

### P1 - Sliding conformity drops the last valid window

**Files**
- [`dynetx/algorithms/assortativity.py`](dynetx/algorithms/assortativity.py#L248)

**Problem**

The loop condition uses:

```python
if t + delta < tids[-1]:
```

This excludes the final window where `t + delta == tids[-1]`, even though that window is valid and should be part of the sliding analysis.

**Why it matters**

The output sequence is incomplete and biased toward earlier windows.

**Priority**

Medium-high. Fix the boundary condition and add a regression test around the last interval.

---

### P1 - Snapshot key remapping is brittle and partly broken

**Files**
- [`dynetx/readwrite/edgelist.py`](dynetx/readwrite/edgelist.py#L299)
- [`dynetx/readwrite/edgelist.py`](dynetx/readwrite/edgelist.py#L303)

**Problem**

`read_ids()` uses `if len(line) == 4:` to decide whether to capture an additional timestamp field. This checks the raw line length in characters, not the number of parsed fields, so it almost never does what the code intends.

It also means `keys=True` remapping can be incorrect for snapshot files, especially when the original file includes both appearance and disappearance timestamps.

**Observed behavior**

```python
from dynetx.readwrite.edgelist import read_ids
# for a normal line like "1 2 3 4\n", the logic does not behave as intended
```

**Why it matters**

Key remapping is used to preserve original timestamp identity across read/write cycles. If it is wrong, imported data can shift its timeline unexpectedly.

**Priority**

Medium-high. Replace the character-length test with token-based parsing and add a round-trip test that includes interval edges.

---

### P2 - Error handling is non-idiomatic and can mask root causes

**Files**
- [`dynetx/readwrite/edgelist.py`](dynetx/readwrite/edgelist.py#L166)
- [`dynetx/readwrite/edgelist.py`](dynetx/readwrite/edgelist.py#L139)
- [`dynetx/readwrite/edgelist.py`](dynetx/readwrite/edgelist.py#L242)

**Problem**

There are multiple places where broad `except:` blocks are used, and one branch raises `NotImplemented` instead of `NotImplementedError`.

Examples:

- `generate_snapshots()` uses `raise NotImplemented`, which is not a valid exception type.
- Timestamp conversion failures report `nodetype` in the error message even when the failure is in `timestamptype`.

**Why it matters**

These paths make debugging harder and can turn malformed input into confusing secondary errors.

**Priority**

Medium. This is mostly about diagnosability and robustness, but it should be cleaned up alongside the I/O fixes.

---

### P2 - Release metadata is inconsistent across packaging files

**Files**
- [`setup.py`](setup.py#L23)
- [`conda/meta.yaml`](conda/meta.yaml#L3)
- [`README.md`](README.md#L23)

**Problem**

The version and citation metadata disagree:

- `setup.py` declares `0.3.2`
- `conda/meta.yaml` declares `0.3.1`
- `README.md` cites `v0.2.1`

**Why it matters**

This creates confusion for release tracking, packaging, and user trust. It also makes it harder to know which artifact is authoritative.

**Priority**

Medium. Fix after the functional bugs, but before any release or documentation refresh.

---

## Phased Remediation Pipeline

### Phase 1 - Stabilize core correctness

Goal: eliminate silent corruption and runtime crashes in core graph APIs.

1. Fix `get_node_snapshots()` in both graph classes.
2. Fix `interactions_per_snapshots()` so it returns integer counts for both instantaneous and interval edges.
3. Add zero-division guards for `coverage()`, `uniformity()`, `node_pair_uniformity()`, and related summaries.
4. Replace `update_node_attr()` and `update_node_attr_from()` with attribute merges instead of overwrites.

Deliverable:
- Regression tests that fail before the patch and pass after it.

### Phase 2 - Repair temporal traversal and analytics

Goal: make path and conformity routines safe for the full node-id space and complete their output windows.

1. Remove underscore-based node decoding in `temporal_dag()`.
2. Make `temporal_dag()` use an explicit temporal-node representation or a structured tuple key.
3. Fix the `sliding_delta_conformity()` window boundary.
4. Add tests for node IDs containing underscores and for the final sliding window.

Deliverable:
- Temporal path analytics that work for arbitrary string node IDs and return complete window coverage.

### Phase 3 - Harden import/export

Goal: make round-trips predictable and debuggable.

1. Fix `read_ids()` token parsing.
2. Replace `raise NotImplemented` with `NotImplementedError`.
3. Remove or narrow broad exception handlers where they hide input problems.
4. Add round-trip tests covering interval edges, removal events, and `keys=True`.

Deliverable:
- Stable read/write behavior for both snapshot and interaction formats.

### Phase 4 - Align metadata and docs

Goal: remove release drift and make the published surface trustworthy.

1. Align version numbers in `setup.py`, `conda/meta.yaml`, and any release notes.
2. Update the README citation to match the released artifact.
3. Audit docstrings and examples for outdated assumptions.

Deliverable:
- Single source of truth for versioning and documentation.

### Phase 5 - Backstop with tests and CI expectations

Goal: keep the fixes from regressing.

1. Add targeted unit tests for every bug above.
2. Add a small set of edge-case tests for empty graphs and malformed input.
3. If possible, run the new tests under the oldest supported Python and NetworkX combinations in CI.

Deliverable:
- A safety net that covers the temporal edge cases this library is most likely to regress on.

## Suggested Priority Order

1. `get_node_snapshots()`
2. `interactions_per_snapshots()`
3. Empty-graph metric guards
4. Temporal DAG underscore handling
5. Node attribute overwrite bug
6. Sliding conformity window boundary
7. Snapshot key remapping and I/O hardening
8. Metadata/version alignment

## Verification Notes

- The current test suite passes as-is, so the issues above are mostly uncovered by tests rather than contradicted by them.
- The probes I ran confirm several of the failures directly:
  - `get_node_snapshots()` returns a scalar instead of a list.
  - `update_node_attr()` overwrites existing node attributes.
  - `coverage()` and `uniformity()` raise `ZeroDivisionError` on an empty graph.
  - `interactions_per_snapshots()` returns fractional counts for interval edges.

