# Decisions before us

A discussion register of the **open** decisions facing the team (threat modeler +
ontology/coworker + backend/joshpearce). Forward-looking only — settled merge mechanics
live in [merge-plan.md](merge-plan.md); the deep dive on vocab is in
[vocab-decision.md](vocab-decision.md); what differs between our work and the coworker's
is in [coworker-comparison.md](coworker-comparison.md).

Each item: **context → options → recommendation → owner**. Recommendations are starting
points for the discussion, not conclusions. Everything is currently demonstrated on the
local `vitaly-changes` branch (nothing pushed).

---

## D1 — Control vocabulary: one model, which one?

**Context.** Two RDF vocabularies for the same concepts grew in parallel: our `:Control`
model (scope + capable/provides/requires + protects) and the coworker's `:CTL_*` /
`:CTL_ControlSet` model. Every merge pays a conversion tax. The concepts are agreed; the
naming/shape is not.

**Options.**
- **A — converge on `:Control`** (superset; what the branch implements & runs).
- **B — converge on `:CTL_*`** (flat `owl:OneOf` set; would need capable-tier/scope/L3
  rebuilt on top).
- **A′ — `:Control` model with `:CTL_`-style names** (compromise if the naming is what's
  liked).

**Recommendation.** **A.** It's the superset, it's already working on both backends, and
it's what was conceptually endorsed. Full analysis + mapping table in
[vocab-decision.md](vocab-decision.md).

**Owner.** Coworker (ontology) + threat modeler. *This one gates most others — settle it first.*

---

## D2 — How are control *requirements* authored: derived or asserted?

**Context.** Two styles coexist on the branch:
- **Derived** (ours): zone-crossing + data-sensitivity **policies** compute
  `:requiresControl` automatically from topology.
- **Hand-asserted** (his): `:requiresControl` written directly on L1/L2 elements
  (`L1_3.ttl`, etc.).

**Options.**
- **Derive everywhere** a policy can express the rule; hand-assertion only for one-offs.
- **Assert everywhere** (simpler, but no "write-once policy" payoff; drifts as the model grows).
- **Both, explicitly** — derivation is the default, assertion is an allowed override.

**Recommendation.** **Both, derivation-first.** Keep policies as the source of truth where
they apply (the project's automation thesis), allow hand-assertion as an escape hatch.
Decide which requirements in the current fixtures should migrate from asserted → derived.

**Owner.** Threat modeler (policy semantics) + coworker.

---

## D3 — Unify the two "satisfaction" notions (the bridge)

**Context.** The biggest conceptual overlap. Two answers to "is this requirement met, and
by what?":
- **His `:ControlSatisfaction`** — hand-asserted links, cross-level (an L2 element
  satisfies an L1 requirement); consumed by the L1/L2 **threat modelers** (✅/⚠️).
- **Our computed grading** — `:protects`/`:providesControl` + capable tier → Open /
  Potential / Mitigated, with **L3/IaC evidence** confirming provision.

Right now they're parallel and disconnected.

**Options.**
- **(a) Grading emits `:ControlSatisfaction`** — our derivation/L3 evidence *produces*
  satisfaction instances; his threat-model renderer consumes them unchanged.
- **(b) Threat modeler reads our grade** — his renderer reads Open/Potential/Mitigated
  (incl. IaC-confirmed) instead of hand-asserted links.
- **(c) Keep both** — accept duplication.

**Recommendation.** **(a).** One producer (policy-derived + IaC-graded), one consumer (his
renderer). A threat then renders not just ✅/⚠️ but ✅-confirmed-by-Terraform / 🟡-potential.
This is the real synergy payoff and the natural next build.

**Owner.** Joint (threat modeler + coworker).

---

## D4 — Level model: how do L1 / L2 / L3 relate for controls?

**Context.** His threat modeler treats **L1 requirements** as the obligation that **L2**
elements must satisfy. Our model derives **L2** obligations from policy and confirms them
with **L3** (IaC) evidence. We haven't agreed the direction explicitly.

**Options.**
- **Requirements flow down, evidence flows up:** L1 states intent → L2 must satisfy → L3
  proves it. (Coherent with both bodies of work.)
- **Each level self-contained:** obligations/evidence stay within a level. (Simpler, loses
  the cross-level story his L2 modeler already does.)

**Recommendation.** **Requirements down / evidence up**, made explicit in the docs and the
queries. This frames D3's bridge and clarifies where `:requiresControl` legitimately lives
at each level.

**Owner.** Threat modeler.

---

## D5 — Backend strategy: GraphDB vs portable rdflib

**Context.** Two backends now work (delegate pattern): GraphDB (`owl2-rl-optimized`,
server) and the portable rdflib backend (`owlrl` `OWLRL_Semantics`, no server). `runall.sh`
is green on both.

**Options.**
- **GraphDB canonical, rdflib for dev/demo** — full engine is source of truth; portable for
  laptops/CI/hackathon.
- **rdflib canonical** — zero-infra simplicity; accept any reasoning differences.

**Recommendation.** **GraphDB canonical, rdflib as the portable/demo path**, and keep
*both* in `runall.sh` so divergence is caught early. **Watch-item:** `owlrl` OWL-RL and
GraphDB's `owl2-rl-optimized` are close but not guaranteed identical — note any inference
that differs.

**Owner.** Backend (joshpearce) + us.

---

## D6 — Control-provider modeling: EdgeGateway vs WAF (one concept or two?)

**Context.** During the merge a modeling overlap surfaced: our `:L2_EdgeGateway`
(an `:APIGatewayContainer` that `:protects` an interface and provides controls) vs his
`:L2_WebFrontEndWAF` (a control provider in `L2_3`). I kept them as two separate elements
to avoid reinterpreting his threat model — but conceptually they're "a thing in front of
an interface that provides controls."

**Options.**
- **Unify** into one provider concept (archetype + `:protects`), used by both the control
  modeler and the threat modeler.
- **Keep distinct** (gateway vs WAF as different archetypes with different default controls).

**Recommendation.** **Unify the mechanism** (one "control provider that protects an
interface"), allowing distinct archetypes (WAF/gateway/proxy) with different `hasValue`
defaults. Removes the redundancy the merge exposed.

**Owner.** Threat modeler.

---

## D7 — Collaboration mechanics & stopping the conversion tax

**Context.** No push access to the coworker's repo; each round we re-convert his `:CTL_*`
to our vocab. That cost grows.

**Options.**
- **Fork + PR** (works without write access) vs **get added as collaborator**.
- **Lock the vocab (D1) first**, then work on a shared branch / agreed naming so neither
  side keeps diverging.

**Recommendation.** Settle **D1** with the coworker, then pick a shared workflow (collaborator
access preferred so we're not re-merging a fork). Until then, this branch is the integration
point.

**Owner.** Whole team.

---

## Suggested discussion order

1. **D1** (vocab) — unblocks everything.
2. **D3 + D4** (satisfaction bridge + level model) — the design core / main payoff.
3. **D2** (requirement authoring) — follows from D3/D4.
4. **D6** (provider modeling) — local cleanup.
5. **D5, D7** (backend, workflow) — supporting decisions.
