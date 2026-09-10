# Miniature ZX-Library Architecture Experiment

## Status

Architecture version 1.2 concluded on 2026-09-10. This independent, time-boxed learning and prototyping exercise was informed by Deltakit issue #319. It is not a funded deliverable, proposed production package, or proposed upstream repository layout. The prototype is preserved as evidence; further implementation requires a separately scoped decision.

## Question

Can a thin corpus layer provide reproducible, bulk-accessible ZX-graph benchmarks from heterogeneous sources while retaining authoritative source identity and provenance, portable QEC summaries, and links to richer semantic representations when needed?

## Outcome

Partially. A thin, source-independent corpus layer works for inputs that can honestly produce a ZX graph. The experiment demonstrated reproducible OpenQASM 2 and graph-native ingestion, immutable source-based identity, minimum provenance admission, heterogeneous registry access, and deterministic transformation lineage.

The graph-centered design does not generalize honestly to realistic Stim/QEC programs. Reset, measurement, detector, observable, and later unitary operations form relationships that cannot be represented by removing non-unitary instructions and concatenating the remaining gates into one coherent ZX graph. Structural graph well-formedness does not recover those omitted semantics.

A future architecture should separate authoritative source artifacts from optional graph extractions. One source could retain portable summaries and richer semantic representations while linking to zero or more scoped ZX graphs and their derived transformations. That refinement was documented but deliberately not implemented within this experiment.

## Original architecture under test

The experiment began with the following graph-centered design. Its QASM, graph-native, registry, identity, provenance, and derivation boundaries were validated, while its universal one-source-to-one-graph assumption was falsified for realistic QEC inputs.

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

### Generated Stim repetition-code Path of Pain

Using official Stim 1.16.0, the experiment generated a deterministic distance-three, two-round repetition-code memory circuit containing five qubits, seven measurements, six detectors, and one observable. Stim preserved target ordering, flattened repeated blocks deterministically, and exposed the required portable counts directly.

The generated circuit interleaves reset, unitary gates, measurement-and-reset, later unitary gates, final measurements, detectors, and an observable. Removing the non-unitary instructions and concatenating the remaining gates would falsely represent the circuit as uninterrupted coherent evolution. Structural ZX-graph well-formedness would not restore the omitted state-preparation, measurement-history, detector, or observable relationships.

This falsifies the naïve one-source-to-one-unitary-graph design for realistic QEC circuits, but does not rule out Stim support. Honest alternatives include richer semantic retention, multiple linked ZX segments, or an explicitly restricted Stim subset. No Stim adapter will be implemented until one of those representation contracts is justified within the experiment’s time box.

### Candidate source-first refinement

The smallest unimplemented refinement would separate authoritative source identity from conversion identity. A source artifact would record the collection, entry, revision, source digest, provenance, and optional portable QEC summary. Zero or more linked graph extractions would separately record their adapter, adapter version, extraction scope, and graph digest.

This could represent multiple computational segments from one QEC source without treating any segment as the complete program. It remains a paper design: implementing segment boundaries and their relationships to resets, measurements, detectors, and observables is not justified without a separately funded or explicitly scoped development decision.

### PyZX serialization Path of Pain

Using pinned PyZX 0.10.6, repeated construction of the same graph with the same vertex insertion order produced byte-identical version-2 JSON and identical SHA-256 digests.

Equivalent well-formed identity graphs constructed with different vertex insertion orders produced equal matrices but different vertex identifiers, JSON representations, and graph digests. PyZX JSON is therefore suitable as a reproducible representation of an exact conversion process, but its digest is not a canonical semantic identity for equivalent ZX graphs.

Importing PyZX 0.10.6 under Deltakit’s warnings-as-errors pytest policy also exposed a Python enum `DeprecationWarning` in PyZX’s routing module. The experiment retains strict warning handling with a narrow exception for that identified upstream warning.

### Deterministic transformation and lineage

Using pinned PyZX 0.10.6, the experiment applied `spider_simp` to a controlled four-vertex graph containing adjacent Z spiders. The transformation reduced the graph to three vertices while preserving structural well-formedness and matrix semantics.

`DerivationBuilder` verifies that supplied parent graph bytes match the digest recorded by the parent artifact before invoking a transformer. It then applies shared hashing and constructs a derived artifact recording the parent identity, transformation name and version, canonical parameters, output format, and output digest. Mismatched parent content is rejected before transformation.

Repeated application to the same parent produced byte-identical version-2 JSON, identical graph digests, and identical derived-artifact identities. The parent remained unchanged. `DerivedGraphResult` returns the serialized output alongside the thin artifact record, keeping content persistence separate from identity and lineage metadata.

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

The minimum automated admission policy permits `NOASSERTION` only with `REFERENCE_ONLY`. `CorpusBuilder` applies this rule before invoking a source adapter, preventing sources with unidentified licensing from being bundled or automatically fetched.

Passing this minimum gate means only that the required provenance and distribution treatment have been declared consistently. It does not determine legal permission or verify that an identified license is compatible with every use.

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

## Planned minimum viable experiment

The experiment was scoped to implement only enough functionality to test these architectural claims:

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

This miniature experiment did not aim to:

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

## Closure audit

| Objective | Outcome |
| --- | --- |
| Assemble 6–10 deliberately diverse entries | Not completed. Additional repetitive fixtures would add volume without resolving another architectural question. |
| Apply provenance, licensing, and reproducibility gates | Demonstrated at experimental scale through required provenance, deterministic hashing, and pre-conversion admission. |
| Import representative OpenQASM 2 | Demonstrated with generated, license-safe unitary fixtures. |
| Import representative Stim/QEC computational content | Partially demonstrated in an earlier qecirc proof of concept; the general one-graph conversion contract was subsequently falsified by a realistic generated repetition-code circuit. |
| Preserve a linked portable QEC summary | Structurally demonstrated through `QecSidecar`; not exercised through a production Stim adapter. |
| Import graph-native input directly | Demonstrated through `PyZXJsonAdapter`. |
| Assign stable identities and hashes | Demonstrated for raw and derived artifacts. |
| Retrieve heterogeneous artifacts through one registry | Demonstrated at miniature in-memory scale. |
| Apply a deterministic transformation with lineage | Demonstrated through `PyZXSpiderSimplifier` and `DerivationBuilder`. |
| Repeat builds and confirm stable identities | Demonstrated for ingestion and derivation paths. |

The experiment did not test lazy or persistent corpus storage, a complete benchmark collection, production-scale licensing review, or a lossless QEC semantic representation. These remain separate design and implementation questions.

## Lessons learned

- Authoritative source identity should be conceptually separate from conversion and graph-extraction identity.
- A reproducible serialization digest identifies an exact conversion result, not the semantic equivalence class of a ZX graph.
- Structural graph well-formedness does not prove that a conversion preserved the source program’s full semantics.
- Thin source-independent builders are useful for applying shared hashing, provenance, and lineage policy consistently.
- Provenance admission can prevent obviously inconsistent distribution treatment, but it does not replace legal or license-compatibility review.
- Raw graph immutability and explicit derived lineage work cleanly when parent content is verified against its recorded digest.
- A narrowly chosen path-of-pain test can be more valuable than expanding a prototype: the realistic Stim circuit exposed the principal architectural limit before substantial implementation effort was spent.

## Final stopping decision

The applicable success criteria have been tested, and a falsifying constraint has been identified for the universal graph-centered design. In accordance with the stop condition, active implementation ends here. The evidence is preserved without expanding the prototype into a complete benchmark product.
