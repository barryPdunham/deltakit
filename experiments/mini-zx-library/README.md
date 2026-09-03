# Miniature ZX-Library Architecture Experiment

## Status

Experimental architecture probe based on Deltakit issue #319. This directory is not a proposed production package or upstream repository layout.

## Question

Can a thin corpus and metadata layer provide reproducible, bulk-accessible ZX-graph benchmarks from heterogeneous circuit sources while preserving source-specific QEC semantics outside the ZX representation?

## Architecture under test

```text
Upstream sources
├── QASM / Benchpress
├── Stim / qecirc
└── Curated graph-only entries
          │
          ▼
Source adapters
          │
          ▼
Immutable raw artifact + metadata + QEC sidecar
          │
          │
          ├── Registry and bulk retrieval
          └── Transformations → derived artifacts with lineage
```

### Core boundaries

1. **Source adapters** convert supported source formats into raw, unsimplified PyZX graphs.
2. **Artifact records** identify each graph and record its provenance, source revision, hashes, licensing, metadata, and representation.
3. **The registry** retrieves individual artifacts or filtered collections in bulk.
4. **Transformations** produce derived artifacts without mutating the imported raw artifact.
5. **QEC sidecars** preserve semantics that cannot be represented faithfully in a unitary ZX graph.

## Architecture rules

1. An imported raw ZX graph is an immutable benchmark artifact.
2. Simplification or rewriting produces a new derived artifact with explicit parentage and transformation metadata.
3. QEC semantics are preserved alongside the ZX representation rather than forced into it.
4. Imports must be reproducible from a pinned upstream revision and source hash.
5. Licensing and provenance are properties of each source artifact, not merely of the Python package.
6. The core data model must not contain source-specific conditional logic.

## Identity strategy

Raw artifacts use two complementary forms of identity:

1. **Source identity** records the source collection, entry identifier, pinned revision, source-file SHA-256 digest, and adapter version.
2. **Graph digest** records the converted graph output for reproducibility checking.

The source-file digest is authoritative for identifying the imported input. The graph digest is initially evidence about conversion reproducibility rather than the sole artifact identity, because graph serialization may depend on incidental vertex ordering or library-specific representation details.

A derived artifact is identified by its parent artifact, transformation name and version, canonicalized parameters, and output graph digest.

## Evidence already obtained

### Benchpress happy path

A prior proof of concept established that a selected Benchpress/QASM circuit could be converted reproducibly into an unsimplified PyZX graph.

Exact circuit identifier, dependency versions, graph counts, and hashes remain to be recovered from the original POC record.

### qecirc Path of Pain

A qecirc/Stim proof of concept reproduced Deltakit’s repeated-target `DuplicateQubitError`. After isolating and correcting that parser issue:

* the QEC circuit imported successfully;
* qubit and measurement counts were preserved;
* detector and observable counts were preserved separately; and
* the circuit’s computational content was converted reproducibly to PyZX.

This demonstrated that the ZX graph alone is not a lossless representation of the original QEC circuit. Detector, observable, measurement, and other non-unitary semantics require a sidecar representation linked to the raw graph artifact.

Exact qecirc sample identifier, counts, dependency versions, and hashes remain to be recovered from the original POC record.

## Implementation refinement: artifact construction

Source adapters interpret source-specific formats but do not independently construct corpus artifacts.

An adapter returns a small internal import result containing the serialized raw graph, its format, and any QEC sidecar. A shared corpus builder then applies the corpus-wide source hashing, graph hashing, adapter identity, and artifact-construction rules.

This keeps source interpretation separate from corpus identity policy and prevents adapters from implementing inconsistent hashing or provenance rules.

The internal import result is visible in this public repository but is not part of the supported public API.

## Provenance policy

Every raw artifact carries a required provenance record containing:

- the upstream URL;
- the source path;
- the upstream license expression;
- a supporting license reference; and
- the corpus distribution mode.

`NOASSERTION` is permitted when no verified license can be identified. This records uncertainty explicitly rather than treating missing license information as permission to redistribute an artifact.

Distribution modes describe corpus behaviour—not legal conclusions:

- `BUNDLED`: the artifact is distributed with the corpus;
- `FETCHED`: the artifact is acquired separately from its upstream source; and
- `REFERENCE_ONLY`: the corpus records the source but does not acquire or redistribute it.

Derived artifacts retain provenance transitively through their parent artifact identity.

## Minimum viable experiment

The experiment will implement only enough functionality to test these architectural claims:

1. Import one representative QASM circuit.
2. Import the computational portion of one representative Stim/QEC circuit.
3. Preserve the Stim/QEC metadata in a linked sidecar.
4. Assign stable identities and hashes to raw artifacts;
5. retrieve both artifacts through one registry API;
6. filter the registry using selected metadata;
7. apply one deterministic ZX transformation;
8. record the derived artifact’s parent and transformation parameters; and
9. repeat the build and confirm identical raw-artifact identities.

Upstream benchmark files should not be committed until their licensing and redistribution terms have been verified. The experiment may initially use generated fixtures or locally acquired source files.

## Success criteria

The architecture passes if:

* heterogeneous sources produce records conforming to one core model;
* repeated imports of identical inputs produce identical raw-artifact identities;
* raw artifacts remain unchanged after transformations;
* derived artifacts retain complete lineage;
* bulk retrieval does not require callers to understand individual adapters;
* relevant QEC counts and annotations survive outside the ZX graph; and
* adding another adapter does not require modifying the core artifact model.

## Falsification criteria

The architecture should be reconsidered if:

* source-specific exceptions accumulate in the core model;
* stable artifact identity depends on incidental serialization details;
* meaningful QEC semantics cannot be linked unambiguously to the converted graph;
* raw and derived artifacts cannot be distinguished reliably;
* provenance cannot identify the exact upstream input;
* bulk retrieval requires eagerly loading the entire corpus; or
* licensing constraints make the proposed distribution model impractical.

## Non-goals

This miniature experiment will not:

* create the complete benchmark corpus;
* define Deltakit’s final package or repository name;
* implement every source adapter;
* reproduce all QEC semantics directly in ZX;
* develop a general ZX rewriting engine;
* optimize benchmark graphs;
* establish performance claims; or
* open an upstream pull request.

## Stop condition

Once the experiment either satisfies a success criterion or exposes a falsifying architectural constraint, preserve the evidence and stop expanding the prototype. Further implementation requires a separate decision.
