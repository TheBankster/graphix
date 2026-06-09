# Control Modeling — Progress

Tracking the work to make security controls first-class, inferable elements of the
GRAPHIX ontology so that threats can be marked **mitigated** (and that mitigation
later **confirmed by L3 evidence**), rather than every threat being emitted
unconditionally with a hard-coded recommended control.

## Background / motivation

Today the threat modeler ([`L1_modeler.py`](../L1_modeler.py)) emits a fixed set of
STRIDE threats for each topology match, each tagged with a *recommended* control
drawn from the `CONTROL` enum in [`controls.py`](../controls.py). Nothing in the
graph records whether that control is actually present, so the modeler can never
say a threat is mitigated — it only ever recommends.

To change that, controls need to exist **in the graph**, not just in Python, so the
ontology and the SPARQL rules can reason over them (e.g. "this API requires Rate
Limiting; is there an element on its path that provides Rate Limiting?").

The broader design (for reference; not all built yet) distinguishes three claims:

- `:requiresControl` — obligation; this element needs the control (born where the threat is born, usually derived by the threat rule).
- `:capableOfControl` — potential; this element/type *could* provide it if configured.
- `:providesControl` — realized; the element actually provides it (confirmed, ultimately by L3 evidence).

A threat's **status** is then the join of obligation against evidence
(Open / Potential-unverified / Mitigated).

---

## Step 1 — Promote the `controls.py` enum into RDF ✅ DONE

**Goal:** make each control a first-class individual in the ontology so the graph
can reference and reason over it.

**Changes:**

1. [`schema.ttl`](../schema.ttl)
   - Added a `:Control` class (under *Classes → Controls (Capabilities)*).
   - Added a **Control Catalog** section enumerating the five controls as
     individuals of `:Control`.
2. [`controls.py`](../controls.py)
   - Added a note pointing to the canonical RDF definition to flag the
     dual representation and the need to keep them in sync.

**Mapping (enum ↔ ontology):** the `rdfs:label` of each individual is the exact
enum *value* string, so the two representations can be cross-checked / round-tripped.

| `CONTROL` enum member  | enum value             | RDF individual          |
|------------------------|------------------------|-------------------------|
| `CLIENT_AUTHENTICATION`| "Client Authentication"| `:ClientAuthentication` |
| `SERVER_AUTHENTICATION`| "Server Authentication"| `:ServerAuthentication` |
| `ACCESS_CONTROL`       | "Access Control"       | `:AccessControl`        |
| `RATE_LIMITING`        | "Rate Limiting"        | `:RateLimiting`         |
| `TRAFFIC_ENCRYPTION`   | "Traffic Encryption"   | `:TrafficEncryption`    |

**Verification:** the catalog is plain RDF triples that parse with the rest of
`schema.ttl`; uploading the schema (`main.py -s schema.ttl`) and querying
`SELECT ?c WHERE { ?c a :Control }` should return the five individuals.

### Known follow-up: drift between enum and ontology

The control set now lives in two places (Python enum + RDF individuals). For now
they are kept in sync by hand and cross-referenced by comments. A later step
should make one the single source of truth (e.g. generate the enum from the
ontology, or vice versa) so they cannot silently diverge.

---

## Step 2 — Add the control relationship properties ✅ DONE

**Goal:** give the graph the vocabulary to express obligations, potential, realized
provision, and positioning, so a threat's mitigation status can be computed.

**Changes:** [`schema.ttl`](../schema.ttl), new *Control Relationships* subsection
under Object Properties:

| Property            | Domain → Range                  | Meaning |
|---------------------|---------------------------------|---------|
| `:requiresControl`  | `:Graphix_Element` → `:Control` | Obligation; element needs the control (usually derived by the threat modeler). |
| `:capableOfControl` | `:Graphix_Element` → `:Control` | Potential; element could provide it if configured. |
| `:providesControl`  | `:Graphix_Element` → `:Control` | Realized; element actually provides it. **`rdfs:subPropertyOf :capableOfControl`**, so providing entails being capable. |
| `:protects`         | `:Graphix_Element` → `:Graphix_Element` | Positioning; subject applies its controls to traffic reaching the object. |

**Design notes:**
- All four are rooted at `:Graphix_Element` (not `:L2_Element`) so they work at any
  level — an L1 Interface or an L2 API can both require/provide controls.
- The `:providesControl ⊑ :capableOfControl` entailment means a confirmed provider
  is automatically counted as capable; only `:providesControl` need be asserted.

**Verification:** `schema.ttl` parses with rdflib; all four properties resolve with
the expected domain/range, and `:providesControl` reports
`subPropertyOf = capableOfControl`.

**Intended satisfaction logic** (query lands in a later step): a `:requiresControl`
on an element is **Mitigated** iff some element `:protects` it and `:providesControl`
the same control; **Potential** iff such a protector is only `:capableOfControl`;
otherwise **Open**.

---

## Step 3 — Add control-provider archetypes ✅ DONE

**Goal:** let component *types* carry their control capability once, so any instance
inherits it under inference — no per-instance control triples.

**Changes:** [`schema.ttl`](../schema.ttl), new *Control-Provider Archetypes* section.
Each archetype is a `:L2_Container` subclass with OWL `hasValue` restrictions:

| Archetype               | Tier         | Controls |
|-------------------------|--------------|----------|
| `:WAF`                  | `providesControl` (by design) | Rate Limiting |
| `:AuthenticationGateway`| `providesControl` (by design) | Client Authentication |
| `:ReverseProxy`         | `capableOfControl` | Rate Limiting, Traffic Encryption, Client Authentication |
| `:APIGatewayContainer`  | `capableOfControl` | Rate Limiting, Client Authentication, Traffic Encryption |
| `:LoadBalancer`         | `capableOfControl` | Traffic Encryption (TLS termination) |

**Design notes:**
- *Provides-by-design vs capable-only* is the security judgment, and it is exactly
  the nginx-vs-WAF distinction: a WAF's job *is* rate limiting (provides); a reverse
  proxy / gateway / LB only does it *when configured* (capable), so the realized
  `:providesControl` must come from L3 evidence.
- This set spans rate limiting, TLS termination, and auth on purpose, to confirm the
  pattern generalises past the original rate-limiting example.

**Verification (with `owlrl` reasoner over `schema.ttl` + a tiny ABox):**
- `:myWaf a :WAF` ⇒ `providesControl :RateLimiting` **and** `capableOfControl :RateLimiting`
  (the latter inferred via `providesControl ⊑ capableOfControl`).
- `:myNginx a :ReverseProxy` ⇒ `capableOfControl {RateLimiting, TrafficEncryption,
  ClientAuthentication}` but `providesControl` **empty** — i.e. capable, not yet realized.

### ⚠️ CONFIRMED ISSUE: the GraphDB ruleset does not materialise `hasValue` ✅ RESOLVED 2026-06-09

> **Resolved** by switching the repo to `owl2-rl-optimized` — see the *Decision record →
> Implementation note*. The box below documents the original RDFS-Plus behaviour.

Tested against the live `GRAPHIX` repo (ruleset = **`rdfsplus-optimized`**):

| Inference | Works? | Evidence |
|-----------|--------|----------|
| `subClassOf`     | ✅ | `:L2_EdgeGateway a :L2_Container` = true |
| `subPropertyOf`  | ✅ | explicit `providesControl` ⇒ `capableOfControl` |
| `owl:hasValue`   | ❌ | archetype capable-only controls **not** propagated to instances |

**Consequence:** under this ruleset the **capable-only tier is inert** — an
`:APIGatewayContainer` instance is *not* inferred `capableOfControl` its configurable
controls, so the POTENTIAL state collapses to OPEN. Only explicit instance-level
`providesControl` / `capableOfControl` triples count. Confirmed end-to-end: in the live
repo `WebFrontEndAPI`'s TrafficEncryption and ClientAuthentication came back **OPEN**,
whereas the local `owlrl` run (full OWL-RL) reported them **POTENTIAL**.

`owl:hasValue` needs an OWL ruleset (`owl-horst` / `owl-max` / `owl2-rl`), **not**
RDFS-Plus. (An earlier draft of this note wrongly grouped RDFS-Plus with OWL-RL; the
live test corrects that.)

**Options (decision pending):**
- **(A)** Switch the repo ruleset to `owl2-rl` / `owl-max` — schema works as designed,
  but reconfigures the repo and re-infers everything; ruleset choice is the coworker's call.
- **(B)** Drop `hasValue`; carry archetype capability as a class-level property and join
  it at query time via `rdf:type` (works under RDFS-Plus).
- **(C)** Keep the `hasValue` schema but materialise it ourselves with a one-off SPARQL
  `INSERT` in the modeler before evaluating satisfaction (ruleset-independent).

### Note: encryption-at-rest is *not* an archetype

Encryption-at-rest is a **node control** (intrinsic to a DataStore), so it is *not*
modeled via a provider archetype + `:protects`. The DataStore provides it on itself.
That requires the control-scope split (`:ChannelControl` / `:NodeControl`), tracked
as a separate next step.

## Step 4 — Zone trust-classification + boundary-crossing policy vocabulary ✅ DONE

**Goal:** make control *requirements* a function of which trust zones a call crosses,
authored once as reusable policy rather than hand-asserted per edge.

**Changes:** [`schema.ttl`](../schema.ttl), new *Zone Trust Classification &
Boundary-Crossing Policy* section.

- **Zone trust archetypes** (subclasses of `:Graphix_TrustBoundary`):
  `:UntrustedZone`, `:PublicZone`, `:ApplicationZone`, `:DataZone`. A concrete zone is
  multi-typed, e.g. `:SomeZone a :L2_TrustBoundary , :PublicZone`.
- **Policy vocabulary:** `:BoundaryCrossingPolicy` with `:crossingFromType`,
  `:crossingToType` (both point at zone *types*), and `:mandatesControl`.
- **Example policy:** `:Policy_Untrusted_to_Public` mandates Traffic Encryption +
  Client Authentication + Rate Limiting. No `Public → Application` policy exists,
  *on purpose* — an internal app-tier hop mandates nothing.

**Design notes:**
- Policies key on zone **types**, so one policy covers every environment (write-once).
- Directional: `from`/`to` are ordered, so ingress and egress can differ.
- Requirements are a **lookup per zone-type pair**, not a numeric-tier rule —
  external→web and web→app are both "one step in", yet have different requirements,
  which a tier comparison could not express.
- *Class-as-value punning:* `:crossingFromType`/`:crossingToType` point at classes
  (`:UntrustedZone`), which is OWL-Full. SPARQL/GraphDB handle it; flagged for review.
- This step is **channel controls only**. Node-control obligations (encryption-at-rest)
  derive from data sensitivity on a node, not from a crossing — separate thread.

**Verification (rdflib SPARQL over `schema.ttl` + a 3-zone ABox):**
- `ext → web` (Untrusted→Public) ⇒ `{ClientAuthentication, RateLimiting, TrafficEncryption}`.
- `web → app` (Public→Application) ⇒ `{}` (no matching policy).

**Deferred to the satisfaction-query step:** the derivation rule that walks each call
edge, reads caller/callee zones, matches a policy, and emits `:requiresControl` on the
flow. The vocabulary and the join are proven; only the Python/SPARQL that materialises
the obligation remains.

## Step 5 — Control-scope classification ✅ DONE

**Goal:** classify each control by *how* its requirement is satisfied, so node
controls (e.g. encryption-at-rest) flow through the same machinery as channel
controls instead of being a special case.

**Changes:**

1. [`schema.ttl`](../schema.ttl)
   - Added `:ChannelControl` and `:NodeControl`, both `rdfs:subClassOf :Control`.
   - Classified every catalog control (each is now `a :Control` + one scope).
   - Added `:EncryptionAtRest` (`a :Control , :NodeControl`).
2. [`controls.py`](../controls.py)
   - Added `ENCRYPTION_AT_REST = "Encryption at Rest"` to keep the enum in sync.

**Classification:**

| Control                | Scope             |
|------------------------|-------------------|
| Rate Limiting          | `:ChannelControl` |
| Traffic Encryption     | `:ChannelControl` |
| Client Authentication  | `:ChannelControl` |
| Server Authentication  | `:ChannelControl` |
| Access Control         | `:NodeControl`    |
| Encryption at Rest     | `:NodeControl`    |

**How scope drives satisfaction (logic lands in the satisfaction-query step):**
- **Channel control** on E → Mitigated iff `∃ P: P :protects E ∧ P :providesControl C`.
- **Node control** on E → Mitigated iff `E :providesControl C` (intrinsic; no `:protects`).

**Design notes:**
- *Access Control* is the hybrid case — modeled as `:NodeControl` (enforced by the
  resource) but could also be delegated to a gate in front; the satisfaction query may
  later allow a protector for it. Flagged for review.
- *Encryption-at-Rest* now rides the same `requires/provides` rails as everything else,
  replacing the old commented-out `:L2_requiresEncryptionAtRest` boolean idea.

**Verification (rdflib SPARQL over `schema.ttl`):**
- `:ChannelControl` ⇒ {Rate Limiting, Traffic Encryption, Client Auth, Server Auth};
  `:NodeControl` ⇒ {Access Control, Encryption at Rest}.
- Every control has exactly one scope (no unclassified, no double-classified).
- Enum ↔ RDF label sets are identical (6 each) — sync invariant holds.

## Step 6 — Wire the model into the L2 test data ✅ DONE

**Goal:** produce a runnable end-to-end example exercising zones → policy → obligations
→ providers → satisfaction state.

**Changes:**

1. [`tests/L2_1.ttl`](../tests/L2_1.ttl)
   - Classified the zones: `:L2_WebFrontEndZone a … , :PublicZone`;
     `:L2_ApplicationZone a … , :ApplicationZone`.
   - **Fixed a pre-existing bug:** the public API invocation referenced the *class*
     `:L2_Actor` instead of the instance `:L2_Customer`. Corrected (also required for
     the actor→untrusted derivation to fire).
   - Added `:L2_EdgeGateway` (`a :APIGatewayContainer`), fully linked
     (`insideTrustBoundary`, `container_to_L1`), `:protects`-ing the web API, with one
     **simulated L3-confirmed** control (`:providesControl :RateLimiting`).
   - Added a node-control obligation `:L2_ProductDatabase :requiresControl :EncryptionAtRest`.
2. [`tests/L2_2.ttl`](../tests/L2_2.ttl) (the "fixes" fixture)
   - Confirmed the gateway's remaining controls (`:providesControl :TrafficEncryption ,
     :ClientAuthentication`) and the database's at-rest encryption — so every obligation
     is met after the fixes load.

**Derivation rule used (channel obligations):** an external `:L2_Actor` caller is treated
as originating in `:UntrustedZone`; the callee's zone type is read from
`:L2_insideTrustBoundary`; a matching `:BoundaryCrossingPolicy` supplies the mandated
controls. *(This rule is still verification-only Python — moving it into the codebase is
the satisfaction-query step.)*

**Verification (reasoner + derivation over `schema.ttl` + the fixtures):**

| State | `L2_1` only (gaps) | `L2_1 + L2_2` (fixed) |
|-------|--------------------|------------------------|
| `WebFrontEndAPI` requires RateLimiting | MITIGATED | MITIGATED |
| `WebFrontEndAPI` requires TrafficEncryption | POTENTIAL | MITIGATED |
| `WebFrontEndAPI` requires ClientAuthentication | POTENTIAL | MITIGATED |
| `ProductDatabase` requires EncryptionAtRest (node) | OPEN | MITIGATED |

Internal hops (Public→Application, e.g. WebFrontEnd→ProcessingEngine) derive **no**
obligations, as intended. All three satisfaction states appear in the gap case, proving
the channel path (provider/protects), the node path (self-provision), and the
zone-crossing derivation all work together.

**Live GraphDB run** (`-c`/`-s`/`-d`/`-a` against the `GRAPHIX` repo):
- The L2 semantic analyzer reports **only** the deliberate L2_1 gaps; `:L2_EdgeGateway`
  is *not* flagged → the wiring is structurally clean.
- The zone-crossing derivation reproduces the same RL/CA/TE obligations on
  `WebFrontEndAPI`.
- **But** satisfaction differs from the local run: RateLimiting = MITIGATED, while
  TrafficEncryption and ClientAuthentication = **OPEN** (not POTENTIAL) — because the
  repo's `rdfsplus-optimized` ruleset does not fire `owl:hasValue` (see the Step 3
  CONFIRMED ISSUE box). This must be resolved before the capable-only tier is usable.

> **Update 2026-06-09:** resolved — the repo now runs `owl2-rl-optimized`, and this
> live run reproduces the local result (TE / CA = POTENTIAL, not OPEN). See the
> *Decision record → Implementation note*.

## Decision record — GraphDB ruleset (Implemented)

**Status:** Implemented · **Proposed:** 2026-06-09 · **Implemented:** 2026-06-09

**Context:** The control model relies on `owl:hasValue` (archetype → instance
capability). The live `GRAPHIX` repo runs `rdfsplus-optimized`, which does not
materialise `hasValue` (see the Step 3 CONFIRMED ISSUE box), so the capable-only tier
is inert.

**Decision:** Switch the repo to **`owl2-rl-optimized`** (keeping `disableSameAs = true`).

**Rationale:**
- The schema is already OWL — beyond `hasValue` it uses `owl:disjointWith` and
  `owl:unionOf`, which RDFS-Plus also under-serves. The repo is running the ontology
  under-powered; this aligns the engine with the authored model.
- The archetype mechanism (assert capability once per class) is the project's
  "universal / write-once" value proposition; RDFS-Plus can't express it.
- Workarounds (class-level capability + query-time join; or self-materialising the
  expansion via SPARQL `INSERT`) push reasoning into imperative code and accrue debt,
  in a project whose thesis is *semantic* automation.
- `owl2-rl` also turns on the disjointness/consistency checking the schema already
  implies — surfaces modeling bugs as a bonus.

**Costs / risks:** larger materialised store + slower loads (negligible at current
scale); stronger reasoning may surface latent inconsistencies; the ruleset is fixed at
repo creation, so the switch requires **recreating** `GRAPHIX` and reloading (data is
only reloadable test fixtures, but it is a shared repo).

**Alternatives considered:** (B) drop `hasValue`, carry capability as a class-level
property joined at query time; (C) keep `hasValue` schema, materialise it via a SPARQL
`INSERT` in the modeler. Both avoid the repo change but move reasoning out of the
declarative layer.

### Implementation note (2026-06-09)

Executed against the live `GRAPHIX` repo (GraphDB **11.3.3 free**). Confirmed the
switch **cannot** be done by editing the ruleset in place:

- `PUT /rest/repositories/GRAPHIX` with `ruleset` changed to `owl2-rl-optimized`
  returns 200 and the config **reports** the new value, but the engine keeps the
  inferencer it compiled at creation. A repo **restart** + full reload did **not**
  change behaviour — `owl:hasValue` still did not fire and the closure was unchanged.
  The config metadata and the active rule set had silently diverged.
- The only thing that worked was **delete + recreate** the repo with
  `owl2-rl-optimized` (then reload schema + fixtures). GraphDB compiles the ruleset
  into the store at creation, so this is mandatory — exactly the "fixed at repo
  creation" caveat in *Costs / risks* above.

**Procedure used** (data is only the reloadable fixtures; config backed up first to
`.graphdb-backup/` — gitignored, not committed):
1. `GET /rest/repositories/GRAPHIX` → save JSON config; set `ruleset` = `owl2-rl-optimized`.
2. `DELETE /rest/repositories/GRAPHIX`, then `POST /rest/repositories` with the edited JSON.
3. Reload: `main.py -s schema.ttl`, then `-d` each fixture (or `tests/runall.sh`).

**Verification (live repo, post-switch):** `owl:hasValue` now materialises —
`:L2_EdgeGateway` (an `:APIGatewayContainer`) is inferred `:capableOfControl`
{RateLimiting, TrafficEncryption, ClientAuthentication}, with only RateLimiting
`:providesControl`. The Step 6 table now reproduces end-to-end on GraphDB (not just
local `owlrl`): the L2_1 gaps report RateLimiting **MITIGATED**, TrafficEncryption /
ClientAuthentication **POTENTIAL** (previously OPEN), EncryptionAtRest **OPEN**; after
loading L2_2 all four are **MITIGATED**. The semantic analyzer flags only the
deliberate L2_1 gaps and surfaces no consistency errors under the stronger ruleset.

## Step 7 — Derivation + satisfaction in the codebase ✅ DONE

**Goal:** move the zone-crossing **derivation** (emit `:requiresControl` from policy)
and the **satisfaction** grading (Open / Potential / Mitigated) out of throwaway
verification Python into the codebase, behind a flag.

**Changes:**

1. [`L2_modeler.py`](../L2_modeler.py) (new) — `L2_ControlModeler()`:
   - `DeriveChannelObligations()` — a SPARQL `INSERT` that walks each call edge, reads
     caller/callee zone types (external `:L2_Actor` ⇒ `:UntrustedZone`), matches a
     `:BoundaryCrossingPolicy`, and asserts its `:mandatesControl` set as
     `:requiresControl` **on the exposed API**. Idempotent / re-runnable.
   - `EvaluateSatisfaction()` — one SPARQL `SELECT` that grades every `:requiresControl`,
     branching on scope: **node** controls satisfied by self `:providesControl`;
     **channel** controls by a protector that `:protects` the element and
     `:providesControl` (Mitigated) / `:capableOfControl` (Potential) it. Uses
     `IF(EXISTS{…})` so multiple protectors don't multiply rows.
2. [`graphdb.py`](../graphdb.py) — added `RunUpdate()` (POST a SPARQL UPDATE).
3. [`main.py`](../main.py) — new `-m` / `--control-modeler` flag.
4. [`tests/runall.sh`](../tests/runall.sh) — runs `-m` after the L2_1 and L2_2 loads.

**Design notes:**
- Obligations land on the **exposed API** (the entry point), matching the wiring
  `:L2_EdgeGateway :protects :L2_WebFrontEndAPI`. There is no reified "flow" object yet.
- Derivation covers **channel** obligations only (node-control derivation lands in
  Step 8). The satisfaction query already grades both scopes.
- The actor⇒Untrusted rule is a `BIND` in the derivation query (a convention), not an
  asserted triple.

**Verification (`main.py -m` against the live `owl2-rl-optimized` repo):**

| Obligation | L2_1 only | + L2_2 |
|------------|-----------|--------|
| WebFrontEndAPI · Rate Limiting (channel) | MITIGATED | MITIGATED |
| WebFrontEndAPI · Traffic Encryption (channel) | POTENTIAL | MITIGATED |
| WebFrontEndAPI · Client Authentication (channel) | POTENTIAL | MITIGATED |
| ProductDatabase · Encryption at Rest (node) | OPEN | MITIGATED |

## Step 8 — Node-control derivation from data sensitivity ✅ DONE

**Goal:** stop hand-asserting node-control obligations (`:requiresControl
:EncryptionAtRest`) and derive them — the node-side mirror of Step 4/7's zone-crossing
derivation, keyed on an *intrinsic* node property (data sensitivity) instead of a
crossing.

**Changes:**

1. [`schema.ttl`](../schema.ttl), new *Data Sensitivity Classification & Node-Control
   Policy* section:
   - `:DataSensitivity` class + individuals `:Public`, `:Internal`, `:Confidential`.
   - `:handlesDataOfSensitivity` (`:Graphix_Element` → `:DataSensitivity`).
   - `:DataProtectionPolicy` + `:appliesToSensitivity`; reuses `:mandatesControl`.
   - Example policy `:Policy_Confidential_Data` mandates `:EncryptionAtRest` +
     `:AccessControl`.
   - Broadened `:mandatesControl` domain to `owl:unionOf (:BoundaryCrossingPolicy
     :DataProtectionPolicy)` so reusing it on node policies doesn't mis-infer them as
     boundary-crossing policies (verified: `:Policy_Confidential_Data` is **not** typed
     `:BoundaryCrossingPolicy`). Uses the same union-domain idiom as `:L1_invokesInterface`.
2. [`L2_modeler.py`](../L2_modeler.py) — `DeriveNodeObligations()` (`INSERT` joining
   node → sensitivity → policy → `:requiresControl` on the node), called from
   `L2_ControlModeler()` alongside the channel derivation.
3. Fixtures: [`tests/L2_1.ttl`](../tests/L2_1.ttl) now asserts
   `:L2_ProductDatabase :handlesDataOfSensitivity :Confidential` (the two obligations
   are derived from it); [`tests/L2_2.ttl`](../tests/L2_2.ttl) confirms
   `:providesControl :EncryptionAtRest , :AccessControl`.

**Design notes:**
- Node controls land on the **node itself** (intrinsic), satisfied by self-provision —
  no `:protects` needed. A node with no sensitivity assigned mandates nothing.
- Both node controls now come from **one** sensitivity assertion, demonstrating the
  write-once-policy payoff on the node side too.

**Verification (`main.py -m`, live `owl2-rl-optimized` repo):**

| Obligation | L2_1 only | + L2_2 |
|------------|-----------|--------|
| WebFrontEndAPI · Rate Limiting (channel) | MITIGATED | MITIGATED |
| WebFrontEndAPI · Traffic Encryption (channel) | POTENTIAL | MITIGATED |
| WebFrontEndAPI · Client Authentication (channel) | POTENTIAL | MITIGATED |
| ProductDatabase · Encryption at Rest (node, **derived**) | OPEN | MITIGATED |
| ProductDatabase · Access Control (node, **derived**) | OPEN | MITIGATED |

## Step 9 — L3 (as-built) extraction from IaC + reconciliation ✅ DONE

**Goal:** close the L3 bridge. Turn real Infrastructure-as-Code (Terraform) into an
*as-built* layer in the graph, use it as **evidence** that promotes obligations from
Potential → Mitigated with real config (not simulated triples), **and** detect where
the as-built and the intended L1/L2 model **don't conform**.

**Design — L3 is its own layer, *linked* to L2 (not merged):** an L3 resource
`:L3_realizes` its L2 counterpart, exactly like the existing `:L2_*_to_L1` cross-layer
links. Merging IaC facts straight onto L2 individuals would have thrown away the
ability to check conformance (you'd be *assuming* the resource and the modeled element
are the same instead of testing it). Conformance = querying across the `:L3_realizes`
link.

**Correspondence (which L3 realizes which L2)** comes from a `graphix_l2` **resource
tag** in the Terraform (developer-declared, "shift-left") and/or a security-owned
overlay of `:L3_realizes` triples loaded via `-d` (threat-modeler-declared, no code,
no edits to the dev's IaC). Crucially, **unmatched is a finding, not a failure**: an
untagged/unmapped resource surfaces as shadow infrastructure.

**Changes:**

1. [`schema.ttl`](../schema.ttl), new *L3 Implementation Layer* section: `:L3_Element`
   (`⊑ :Graphix_Element`), `:L3_realizes` (`:L3_Element` → `:L2_Element`),
   `:L3_awsResourceType` (provenance). Control evidence reuses the existing
   `:providesControl` vocabulary — no new property.
2. [`L3_extractor.py`](../L3_extractor.py) — `ExtractIaC()`: runs `terraform plan` +
   `terraform show -json` (so Terraform resolves all vars/refs), then maps each
   *significant* resource (api gw, lb, ecs service, db — not plumbing) to an
   `:L3_Element`, reading the `graphix_l2` tag for `:L3_realizes` and concrete config
   for control evidence. Writes `tests/L3_extracted.ttl` (gitignored; regenerated).
   - **Offline-plan trick:** drops a throwaway `zz_graphix_override.tf` with the AWS
     provider `skip_*` flags so `plan` doesn't call STS (this is test data, never
     applied); the override is deleted in a `finally`, leaving the fixture untouched.
   - **Evidence rules:** `aws_db_instance storage_encrypted=true` ⇒ `:EncryptionAtRest`;
     `aws_apigatewayv2_api` ⇒ `:TrafficEncryption` (managed TLS endpoint), plus
     `:ClientAuthentication` *iff* an `aws_apigatewayv2_authorizer` exists; `aws_lb` ⇒
     `:TrafficEncryption` iff it has an HTTPS listener. Absence of an authorizer / WAF
     is exactly what leaves CA/RL unrealized — the gaps are real, not hand-authored.
3. [`L3_analyzer.py`](../L3_analyzer.py) — `L3_Reconciler()`:
   - `PropagateControlEvidence()` — `INSERT` lifting `:providesControl` across
     `:L3_realizes` onto the L2 element, so Step 7 grading runs on real evidence.
   - `ShadowInfrastructure()` — L3 elements that realize nothing modeled (deployed but
     not modeled).
   - `UnrealizedModel()` — L2 containers nothing realizes (modeled but not deployed),
     **excluding actors** (see ontology note below).
4. [`main.py`](../main.py) — `-x`/`--extract-iac DIR` (extract + load) and
   `-r`/`--reconcile` (propagate + conformance report).
5. [`tests/runall.sh`](../tests/runall.sh) — inserts `-x ../terraform`, `-r`, `-m` on
   the L2_1 gap state (before the L2_2 manual-fix path).
6. Terraform fixture: `graphix_l2` tags added to the api gateway, both ECS services,
   and the RDS instance; the internal ALB is **left untagged on purpose** to produce
   the shadow-infra finding.

**Verification (`runall.sh`, live `owl2-rl-optimized` repo) — L2_1 gap state, before vs after L3:**

| Obligation | L2_1 only | + L3 reconcile (real IaC) |
|------------|-----------|---------------------------|
| WebFrontEndAPI · Rate Limiting (channel) | MITIGATED | MITIGATED |
| WebFrontEndAPI · Traffic Encryption (channel) | POTENTIAL | **MITIGATED** (api gw TLS) |
| WebFrontEndAPI · Client Authentication (channel) | POTENTIAL | POTENTIAL (no authorizer) |
| ProductDatabase · Encryption at Rest (node) | OPEN | **MITIGATED** (`storage_encrypted`) |
| ProductDatabase · Access Control (node) | OPEN | OPEN (no IAM DB auth) |

Conformance on the same run: **shadow infrastructure** = `webapp-prod-alb` (`aws_lb`,
untagged, in-path but absent from the model); no false "unrealized" findings.

**⚠️ Ontology note for the coworker (flagged, not changed):** `:L2_invokesAPI` has
`rdfs:domain :L2_Container`, so asserting `:L2_Customer :L2_invokesAPI …` makes OWL-RL
*infer* the customer is an `:L2_Container` (it's really an `:L2_Actor`). This already
makes the L2 semantic analyzer flag the customer as a container "missing a trust
boundary"; it also forced `UnrealizedModel()` to exclude `:L2_Actor` explicitly. The
clean fix is in the schema (e.g. a dedicated `:invokes` for actors, or relaxing the
domain) — that's ontology turf, deferred.

## Next steps (not started)

### Front-end intake: artifacts → L2 model (the mirror of the L3 extractor)

The pipeline is currently **asymmetric**: the *as-built* end (L3) is automated
(`-x`, Terraform → graph), but the *intended* end (L1/L2) is hand-authored Turtle.
The symmetric next move is an **intake extractor for the intended model** — same shape
as the IaC extractor (*artifact → L2 ontology*), but over fuzzier, dev-authored input.

- [ ] **Diagram / artifact → L2 extractor**, with a **mandatory human-in-the-loop**.
      Unlike `-x` (structured, deterministic IaC), diagram input is ambiguous — a box
      could be a container, a zone, or an actor; an arrow may or may not be a
      trust-boundary crossing. So the flow is *extractor proposes → developer
      annotates/corrects*, not full automation.
  - **Annotation is the `graphix_l2` idea pointed the other way:** on the IaC side a
    tag says "this resource *realizes* that modeled element"; on the diagram side the
    annotation says "this box *is* an `:ApplicationZone` / `:L2_DataStore` / `:L2_Actor`."
    Same correspondence concept, authored at the source instead of at deployment.
  - **Candidate inputs (easiest → richest):** structured diagrams (draw.io / Mermaid /
    PlantUML, or pytm-style threat-model-as-code) → mostly a mapping + light annotation
    job; image diagrams (PNG) → vision/LLM extraction, powerful but lossy, leans hardest
    on the human checkpoint; other structured artifacts (OpenAPI, K8s manifests) → could
    feed L2 directly like IaC.
  - **Generalizes the conformance story to three-way:** once devs build L2 from diagrams
    *and* L3 is extracted from their IaC, both describe the same system from two angles —
    intended-by-architect vs. intended-by-dev-diagram vs. as-built. Whose "intended" wins
    is a modeling decision (coworker / ontology turf).

### Other threads

- [ ] Correspondence overlay + heuristic auto-suggest (match by resource type + name)
      so a seceng can reconcile IaC they can't tag at the source.
- [ ] Property-drift conformance: L3 realizes L2 but their facts disagree (e.g. an L2
      DataStore expected in `:DataZone` whose RDS sits in a public subnet).
- [ ] Extract topology/zones from IaC (subnet tiers → zones) toward generating the L2
      ABox, not just control evidence.
- [ ] (Optional) Align controls to a standard catalog (NIST 800-53 / CIS) via SKOS.
