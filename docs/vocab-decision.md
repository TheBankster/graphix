# Control vocabulary — one decision, two paths

**For discussion with the team.** We have two RDF vocabularies for the same idea
(controls, requirements, provision, satisfaction), authored in parallel. They must
converge to one. This doc states *why*, lays out the *two paths*, and points at running
code so we can compare **code and vocabulary together**, not in the abstract.

The `vitaly-changes` branch currently implements **Path A** end-to-end (both backends,
full `runall.sh` green) — so Path A is reviewable as working code today; Path B is
described here as the alternative.

---

## Why this needs deciding now

Both bodies of work converged on the same concepts from different directions:

- **Coworker:** `:CTL_*` controls in an `owl:OneOf` `:CTL_ControlSet`, with
  `:CTL_RequiresControls` / `:CTL_ProvidesControls`, and now a reified
  `:CTL_ControlSatisfaction` consumed by the L1 + L2 **threat modelers**.
- **Us:** `:Control` (+ `:ChannelControl`/`:NodeControl` scope) with
  `:requiresControl` / `:capableOfControl` / `:providesControl` / `:protects`, plus
  zone/data **policies** that *derive* requirements, a **satisfaction grade**
  (Open/Potential/Mitigated), and an **L3/IaC evidence** bridge.

They overlap in purpose but differ in names and shape. Every merge so far has paid a
**conversion tax** (translating one side's `:CTL_*` to the other's `:Control`), and it
grows each round. One vocabulary ends that.

The concept set is **not** in dispute — the coworker endorsed
`requires/capable/provides/protects`. This is purely about which *names/shapes* become
canonical.

---

## The two paths

### Path A — converge on the `:Control` model (what the branch implements)

Controls are first-class `:Control` individuals, scoped `:ChannelControl`/`:NodeControl`;
requirement/provision via `:requiresControl` / `:capableOfControl` / `:providesControl`
(+ `:protects`); the coworker's reified satisfaction kept as `:ControlSatisfaction`.

- **Cost (coworker side):** rename `:CTL_*` → `:Control` vocab in `modeler.py`,
  `L2_modeler.py`, `L1_3.ttl`, `L2_3.ttl`, schema (mechanical; already done on the branch).
- **Gain:** keeps the capability tier (`capableOfControl` → POTENTIAL), control scope,
  policy-derived requirements, and the L3 IaC-evidence bridge — all of which the
  `:CTL_ControlSet` enumeration can't express without being rebuilt.
- **Status:** ✅ implemented and validated on `vitaly-changes` (GraphDB **and** rdflib
  backends); his threat modelers run unchanged in behavior on the converted vocab.

### Path B — converge on the `:CTL_*` model

Controls as `:CTL_*` individuals in `:CTL_ControlSet` (`owl:OneOf`); requirement/provision
via `:CTL_RequiresControls` / `:CTL_ProvidesControls`; satisfaction via
`:CTL_ControlSatisfaction`.

- **Cost (our side):** rename our vocab to `:CTL_*`, **and** re-introduce on top of it the
  things the flat enumeration doesn't have: the `capableOfControl` tier (POTENTIAL),
  `:ChannelControl`/`:NodeControl` scope, `:protects`, and re-point the policies + L3
  bridge. This is more than a rename — it rebuilds capability we'd be discarding.
- **Gain:** keeps the coworker's `owl:OneOf` closed-set as the primary modeling device
  (a clean "controls are exactly these six" statement).
- **Status:** not implemented.

---

## Vocabulary mapping (the rename, either direction)

| Concept | Path A (`:Control`) | Path B (`:CTL_*`) |
|---|---|---|
| Control individual | `:ClientAuthentication` … (a `:Control`) | `:CTL_ClientAuthentication` (in `:CTL_ControlSet`) |
| In-transit encryption label | `Traffic Encryption` | `Data-in-transit Encryption` |
| At-rest encryption label | `Encryption at Rest` | `Data-at-rest Encryption` |
| "needs control" | `:requiresControl` (→ `:Control`) | `:CTL_RequiresControls` (→ `:CTL_ControlSet`) |
| "provides control" | `:providesControl` | `:CTL_ProvidesControls` |
| "could provide if configured" | `:capableOfControl` *(no equivalent)* | — |
| control scope | `:ChannelControl` / `:NodeControl` *(no equivalent)* | — |
| positioning | `:protects` *(no equivalent)* | — |
| reified satisfaction | `:ControlSatisfaction` (+ `:satisfiesRequirementOf` / `:isSatisfiedBy` / `:satisfiedControl`) | `:CTL_ControlSatisfaction` (+ `:CTL_*`) |
| closed-set guard | `allValuesFrom :Control` (kept) | `owl:OneOf :CTL_ControlSet` |

The rows with "no equivalent" are the crux: Path A is a **superset** — Path B would have
to add those to reach feature parity, Path A already has them.

---

## Recommendation

**Path A.** It's the superset, it's what was conceptually endorsed, and it's already
working on the branch on both backends — so the team can review *running* code and the
vocabulary at the same time and decide with evidence rather than on paper. If the team
prefers the `:CTL_*` naming aesthetically, the cheaper compromise is **Path A's model with
`:CTL_`-style names** (a naming pass), rather than Path B's flatter shape.

Open follow-on regardless of choice: **bridge the two satisfaction notions** — his
reified `:ControlSatisfaction` (hand-asserted) and our derived/graded satisfaction
(policy + capability + L3 evidence) should become one (our grading could *emit*
satisfaction instances, or his threat modeler could *read* our grade). See
[merge-plan.md](merge-plan.md).
