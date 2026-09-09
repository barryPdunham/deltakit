# Miniature ZX-Library Architecture Experiment

## Status

Architecture version 1.2. This is an independent, time-boxed learning and prototyping exercise informed by Deltakit issue #319. It is not a funded deliverable, proposed production package, or proposed upstream repository layout.

## Question

Can a thin corpus layer provide reproducible, bulk-accessible ZX-graph benchmarks from heterogeneous sources while retaining authoritative source identity and provenance, portable QEC summaries, and links to richer semantic representations when needed?

## Architecture under test

```text
Upstream sources
├── QASM / Benchpress
├── Stim / qecirc
└── Curated graph-native entries
          │
          ▼
Source-specific adapters
          │
          ├── optional richer semantic representation
          ├── portable metadata and QEC summary
          └── raw, unsimplified ZX graph
                          │
                          ▼
                  Shared corpus builder
                          │
                          ▼
              Immutable raw ZX artifact
                          │
                          ├── registry and bulk retrieval
                          └── transformations → derived artifacts
```

### Core boundaries

1. **Source adapters** interpret supported source formats and produce raw, unsimplified ZX graphs. They may use richer intermediate representations when appropriate.
2. **Artifact records** identify each graph and record its provenance, source revision, hashes, licensing, metadata, and representation.
3. **The registry** retrieves individual artifacts or filtered collections in bulk.
4. **Transformations** produce derived artifacts without mutating the imported raw artifact.
5. **QEC sidecars** provide portable, searchable summaries of QEC context. They do not replace the authoritative source or a richer semantic representation.
6. **Semantic representations** such as Deltakit IR are optional and remain outside the source-independent corpus core.

## Architecture rules

1. An imported raw ZX graph is an immutable benchmark artifact.
2. Simplification or rewriting produces a new derived artifact with explicit parentage and transformation metadata.
3. The original source remains authoritative for semantics not represented by the ZX graph.
4. Portable summaries and optional richer representations are linked alongside the ZX graph rather than forced into it.
5. Imports must be reproducible from a pinned upstream revision and source hash.
6. Licensing and provenance are properties of each source artifact, not merely of the Python package.
7. The core data model must not contain source-specific or compiler-specific conditional logic.

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

### OpenQASM 2 conversion boundary

Using generated, license-safe fixtures, the experiment confirmed that pinned PyZX 0.10.6 converts supported unitary OpenQASM 2 circuits into well-formed version-2 JSON graphs reproducibly. Repeated conversion of identical source content produced byte-identical graph serialization.

PyZX also accepts OpenQASM 2 `measure` and `reset` operations and converts them into structurally well-formed graphs. Those graphs contain symbolic parameters representing non-unitary semantics and cannot be converted into concrete matrices. The initial `OpenQasm2Adapter` therefore rejects measurement and reset rather than silently discarding or misrepresenting them.

For this experiment, “raw” or “unsimplified” means that the adapter applies no post-conversion ZX rewrite or simplification pass. PyZX may still normalize source-level operations during parsing; for example, an identity gate may not remain as an explicit graph operation. The pinned source artifact remains authoritative.

### qecirc Path of Pain

A qecirc/Stim proof of concept reproduced Deltakit’s repeated-target `DuplicateQubitError`. After isolating and correcting that parser issue:

* the QEC circuit imported successfully;
* qubit and measurement counts were preserved;
* detector and observable counts were preserved separately; and
* the circuit’s computational content was converted reproducibly to PyZX.

This demonstrated that the ZX graph alone is not a lossless representation of the original QEC circuit. The original Stim source remains authoritative for detector, observable, measurement, and other non-unitary semantics. A linked sidecar can expose a portable summary, while a richer semantic representation may be retained when justified.

Exact qecirc sample identifier, counts, dependency versions, and hashes remain to be recovered from the original POC record.

### PyZX serialization Path of Pain

Using pinned PyZX 0.10.6, repeated construction of the same graph with the same vertex insertion order produced byte-identical version-2 JSON and identical SHA-256 digests.

Equivalent well-formed identity graphs constructed with different vertex insertion orders produced equal matrices but different vertex identifiers, JSON representations, and graph digests. PyZX JSON is therefore suitable as a reproducible representation of an exact conversion process, but its digest is not a canonical semantic identity for equivalent ZX graphs.

Importing PyZX 0.10.6 under Deltakit’s warnings-as-errors pytest policy also exposed a Python enum `DeprecationWarning` in PyZX’s routing module. The experiment retains strict warning handling with a narrow exception for that identified upstream warning.

## Implementation refinement: artifact construction

Source adapters interpret source-specific formats but do not independently construct corpus artifacts.

An adapter returns a small internal import result containing the serialized raw graph, its format, and an optional portable QEC summary. A shared corpus builder then applies the corpus-wide source hashing, graph hashing, adapter identity, and artifact-construction rules.

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

## Compiler-stack findings

Deltakit-compile 0.1.0 uses an xDSL/MLIR-based compiler stack containing multiple levels of QEC representation. Its IR can represent measurements, detectors, observables, stabiliser flows, quantum effects, noise, and other relationships that cannot be preserved by a ZX graph or by summary counts alone.

The experiment therefore does not assume that every source should be normalized directly into a ZX graph plus metadata. A source adapter may use a richer semantic representation, including Deltakit IR, when appropriate. That representation is optional and is not part of the corpus core model.

The corpus must not depend directly on unstable compiler dialect internals. The authoritative imported input remains the pinned source artifact identified by its source digest and provenance. A retained intermediate representation, if any, is a separately versioned semantic artifact whose source lineage, compiler version, and serialization version must be recorded.

`QecSidecar` is currently a portable, searchable summary of QEC context. It is not a lossless substitute for the original source or a richer compiler IR. ZX graphs remain extracted computational artifacts and do not claim to represent the complete QEC program.

## Minimum viable experiment

The experiment will implement only enough functionality to test these architectural claims:

1. Assemble 6–10 deliberately diverse entries, including QASM, Stim/QEC, and graph-native inputs.
2. Apply provenance, licensing, and reproducibility admission gates to every entry.
3. Import at least one representative QASM circuit.
4. Import the computational portion of at least one representative Stim/QEC circuit.
5. Preserve a portable QEC summary while retaining an unambiguous link to the authoritative source.
6. Import at least one graph-native entry without forcing it through a circuit representation.
7. Assign stable identities and hashes to raw artifacts.
8. Retrieve heterogeneous artifacts through one registry API and filter them using selected metadata.
9. Apply one deterministic ZX transformation and record the derived artifact’s parent and transformation parameters.
10. Repeat the build and confirm identical raw-artifact identities.

A Deltakit-aware adapter may use compiler IR when it adds demonstrable value, but the experiment will not require Deltakit IR as its universal input or persistence model.

Upstream benchmark files must not be committed until their licensing and redistribution terms have been verified. The experiment may use generated fixtures or locally acquired source files where redistribution is not permitted.

## Success criteria

The architecture passes if:

* heterogeneous circuit and graph-native sources produce records conforming to one core model;
* repeated imports of identical inputs produce identical raw-artifact identities;
* raw artifacts remain unchanged after transformations;
* derived artifacts retain complete lineage;
* bulk retrieval does not require callers to understand individual adapters;
* portable QEC summaries remain linked unambiguously to their authoritative sources;
* richer semantic representations can be used without coupling the corpus core to compiler internals;
* every admitted entry has explicit provenance, licensing status, and distribution policy; and
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
* establish performance claims;
* open an upstream pull request;
* adopt Deltakit IR as a universal interchange format; or
* complete the discovery or implementation work contemplated by issue #319.

## Stop condition

Stop when the applicable success criteria have been tested and the architectural question has been answered, or when a falsifying constraint appears. Preserve the evidence without expanding the prototype into a complete benchmark product. Further implementation requires a separate decision.
