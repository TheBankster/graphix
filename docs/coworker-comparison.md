# Coworker comparison — his `origin/master` vs our working tree

Snapshot date: 2026-06-09. Common base: `3f83f93` ("Add script to run all tests at once").

- **His work** = 8 commits on `origin/master` (`3f83f93..3f58bd6`), fetched, not merged.
- **Our work** = uncommitted working tree (8 modified tracked files + untracked
  `L2_modeler.py`, `L3_extractor.py`, `L3_analyzer.py`, `docs/`, `terraform/`).

Everything below is from read-only diffs; nothing was stashed, merged, or committed.

---

## TL;DR — the three headline divergences

1. **`:L2_API` → `:L2_Interface` rename (his).** He renamed the L2 endpoint concept
   from API to Interface across schema, analyzer, and all L2 fixtures. We kept `:L2_API`
   and built `L2_modeler.py` + the L3 extractor on top of it. **This is the biggest
   mechanical conflict** — it touches every L2 file on both sides.

2. **Two different ontology designs for the *same* requires/provides idea.** We both put
   control requires/provides on `:Graphix_Element`, but modeled it differently (his:
   an `owl:OneOf` `:CTL_ControlSet` enumeration; ours: a `:Control` class hierarchy with
   a 3-tier requires/capable/provides + policies + archetypes + L3 evidence).

3. **Different halves of the pipeline.** His advance is a **mitigation-aware L1 *threat*
   modeler** (each threat now renders ✅ mitigated / ⚠️ open by reading required controls).
   Ours is an **L2 *control* modeler** (derive obligations from policy, grade
   Open/Potential/Mitigated, confirm from IaC). They meet at requires/provides but barely
   overlap in code — largely **complementary**.

---

## File-by-file

### Files BOTH touched (merge attention needed)

| File | His change | Our change | Conflict? |
|------|-----------|------------|-----------|
| `schema.ttl` | Added `:CTL_*` individuals + `:CTL_ControlSet` (`owl:OneOf`) + `:CTL_RequiresControls`/`:CTL_ProvidesControls` with `allValuesFrom` restrictions; **renamed `:L2_API`→`:L2_Interface`** (+ `invokesInterface`/`exposesInterface`/`Interface_to_L1`); re-parented `:L2_TrustBoundary` under `:Graphix_TrustBoundary` | Added `:Control`+`:ChannelControl`/`:NodeControl`, control individuals, `:requiresControl`/`:capableOfControl`/`:providesControl`/`:protects`, provider archetypes (`owl:hasValue`), zone archetypes + boundary-crossing & data-sensitivity policies, the L3 layer (`:L3_Element`/`:L3_realizes`) | **Yes** — two control vocabularies in the same namespace + the API/Interface rename |
| `controls.py` | `DATA_IN_TRANSIT_ENCRYPTION` / `DATA_AT_REST_ENCRYPTION` | `TRAFFIC_ENCRYPTION` + added `ENCRYPTION_AT_REST` | **Yes** — same two controls, different labels |
| `main.py` | Split `-a` into `-1` (L1) / `-2` (L2); dropped combined analyze | Kept `-a` (combined L1+L2); added `-m`/`-x`/`-r` | **Yes** — different flag scheme |
| `tests/L2_1.ttl` | API→Interface rename throughout | Zone classification, actor-instance fix, EdgeGateway provider, data sensitivity, `graphix_l2` tags | **Yes** — same fixture, divergent edits |
| `tests/L2_2.ttl` | API→Interface rename | Confirmed provider controls (TE/CA/EaR/AC) | **Yes** |
| `tests/runall.sh` | `-1`/`-2` flags; loads `L1_3.ttl`; no L2-control/L3 steps | `-a`/`-m`; added `-x`/`-r` L3 steps | **Yes** |
| `L2_modeler.py` | **New, committed** — an *L2 threat* modeler (STRIDE), currently a **stub** (header only) | **New, untracked** — an *L2 control* modeler (derivation + satisfaction), fully built | **Yes** — same filename, different purpose. **Git will refuse a merge here** (untracked vs committed) until resolved |

### His-only files (no conflict; we didn't touch them)

| File | His change |
|------|-----------|
| `L1_modeler.py` | Big rework: each STRIDE rule now reads `:CTL_RequiresControls` via `OPTIONAL`/`BIND` and carries a **mitigated bool**; `RenderResults` groups by threat and prints ✅/⚠️ per link. This is the *consumer* of his control model. |
| `L2_analyzer.py` | API→Interface rename in all queries; added type-guard triples inside `NOT EXISTS` (binds the variable so the filter is correct); cosmetic 🎈→✅ |
| `L1_analyzer.py` | Cosmetic only (🎈→✅) |
| `tests/L1_3.ttl` | **New** — hand-asserts `:CTL_RequiresControls` on L1 interfaces/platform, feeding his threat modeler's mitigation check |
| `tests/L1_2.ttl` | Comment wording only |

### Our-only files (no conflict; he doesn't have them)

| File | Our change |
|------|-----------|
| `L3_extractor.py` | **New** — Terraform → L3 `:L3_Element`s (`-x`) |
| `L3_analyzer.py` | **New** — L3↔L2 reconcile: evidence propagation + conformance (`-r`) |
| `graphdb.py` | Added `RunUpdate()` (SPARQL UPDATE) |
| `.gitignore` | Added generated-artifact / terraform ignores |
| `docs/` | `control-modeling.md` (Steps 1–9), this file |
| `terraform/` | Sample IaC test fixture (+ `graphix_l2` tags) |

---

## The control model, side by side (the conceptual core)

| Aspect | His | Ours |
|--------|-----|------|
| Controls in RDF | `:CTL_*` `owl:NamedIndividual` inside an `owl:OneOf` `:CTL_ControlSet` | `:ClientAuthentication` … as individuals of a `:Control` class, sub-typed `:ChannelControl`/`:NodeControl` |
| Requires / provides | `:CTL_RequiresControls`, `:CTL_ProvidesControls` (range = the set), `allValuesFrom` guard | `:requiresControl`, `:capableOfControl`, `:providesControl` (sub-property chain), plus `:protects` for positioning |
| How "requires" is set | **Hand-asserted** in the data (e.g. `L1_3.ttl`) | **Derived** from policy (zone-crossing + data-sensitivity rules) |
| Mitigation states | Binary (required-and-present ✅ / not ⚠️), evaluated in the L1 threat modeler | Three-state (Open / Potential / Mitigated) via the `capable` vs `provides` tiers |
| Evidence source | The graph data | The graph data **+ real IaC** (L3 bridge) |
| Conformance (as-built vs model) | — | Yes (shadow infra, unrealized) |
| Trust zones / policies | — | Yes (zone archetypes + boundary-crossing & data-sensitivity policies) |
| Provider archetypes | — | Yes (`owl:hasValue`; needs `owl2-rl`) |

**Shared philosophy:** controls are first-class graph individuals; requires/provides
hang off `:Graphix_Element`. **Divergence:** his is flatter and hand-asserted, consumed
by a *threat* modeler that flags each threat mitigated-or-not; ours is inference-heavy
(derive requirements from policy, grade with a capable tier, confirm from IaC).

---

## Practical notes for a future merge (not done yet)

- **API vs Interface** is the gating decision — it ripples through every L2 file on both
  sides. Pick one term first, then everything else rebases onto it.
- **One control vocabulary, not two.** Reconcile `:CTL_*`+`:CTL_ControlSet` vs
  `:Control`+`:ChannelControl/:NodeControl`, and the label clash
  (`Data-in-transit`/`Data-at-rest` vs `Traffic Encryption`/`Encryption at Rest`).
- **Rename one `L2_modeler.py`.** His = L2 threat modeler (stub), ours = L2 control
  modeler. Suggest `L2_threat_modeler.py` / `L2_control_modeler.py`.
- **`main.py` flags** need a single scheme (his `-1`/`-2` + our `-m`/`-x`/`-r`).
- **Potential synergy:** his mitigation-aware threat modeler is the natural *consumer*
  of our derived obligations + IaC evidence — his "is this control required?" could read
  our derived `requiresControl`, and his ✅/⚠️ could read our Mitigated/Open grade.
