# Reconciliation / merge plan — our work + coworker's `origin/master`

Companion to [coworker-comparison.md](coworker-comparison.md). Goal: land both bodies of
work on one branch with a single shared vocabulary, then exploit the synergy (his
mitigation-aware threat modeler consuming our derived obligations + IaC evidence).

Nothing here is executed yet. Schema/ontology decisions are marked **[coworker]** — they
own the ontology, so those need their sign-off (the rest is our threat-modeling side).

---

## STATUS: P0–P1 DONE (2026-06-09)

Merged on local branch **`vitaly-changes`** (commit `711a08e`, merge of our WIP
`7fafc75` + his `3f58bd6`). Not pushed (no write access to his repo yet).

**Done:** control vocab unified on **our `:Control` model** (his `:CTL_*`/`:CTL_ControlSet`
dropped; his closed-set `allValuesFrom` guard re-expressed over our vocab); his
`L1_modeler.py` + `L1_3.ttl` converted from `:CTL_*` to our control individuals; adopted
his **`:L2_Interface`** rename and ported our control modeler + fixtures onto it; our
`L2_modeler.py`→`L2_control_modeler.py` (his `L2_modeler.py` threat-modeler stub kept);
`main.py` flags unified (`-1`/`-2` + `-m`/`-x`/`-r`); kept our control labels. **Validated:**
`runall.sh` green — his grouped threat rendering + our L2 grading + L3 evidence/conformance
all run on one schema; his threat modeler confirmed to read our `:requiresControl` (flips
DoS/Spoofing to ✅ when `L1_3` loads).

**Still open (P2/P3):**
- **Cross-level scoping:** our `EvaluateSatisfaction` grades *every* `:requiresControl`
  regardless of level, so loading `L1_3` (L1 obligations) before the L2 grading mixes L1
  items into the L2 report. `runall.sh` deliberately doesn't load `L1_3` before the L2
  steps. Fix = scope grading by level; then both `:requiresControl` consumers coexist.
- **P2 synergy proper:** his threat modeler consumes our *derived* obligations + the
  Open/Potential/Mitigated grade (incl. IaC-confirmed), not hand-asserted binaries.
- **P3:** then push/PR (needs repo access — fork+PR or he adds the collaborator).

## Round 2 — DONE (merged `526152e`, converged on Path A)

His 4 commits (**portable rdflib backend**, **implemented L2 threat modeler**,
**`:CTL_ControlSatisfaction`**) are merged on `vitaly-changes` and converted to our
`:Control` vocabulary (Path A — see [vocab-decision.md](vocab-decision.md)). Done:
- rdflib backend integrated — added `RunUpdate` + delegated it; switched inference to
  `OWLRL_Semantics` (so `owl:hasValue` fires). **`runall.sh` validated on both backends.**
- His L2 threat modeler + `modeler.py` kept; `:CTL_*` / `URI_TO_CONTROL` / labels → our vocab.
- `:CTL_ControlSatisfaction` → our `:ControlSatisfaction`.
- `EvaluateSatisfaction` level-scoped to `:L2_Element` (the Round-1 P2 fix).

**Still open:** the **ControlSatisfaction bridge** (his hand-asserted satisfaction vs our
derived/graded one — unify into one); inbound/outbound threat-semantics review; then
push/PR once repo access exists. The original forward plan that produced this is kept
below for reference.

### Original Round-2 forward plan (for reference)

His next 4 commits add a **portable rdflib backend**, an **implemented L2 threat
modeler**, and a **`:CTL_ControlSatisfaction`** model. Full breakdown in
[coworker-comparison.md](coworker-comparison.md) (Round 2 section). Plan:

### Decision that now needs a real answer: the vocabulary (escalated)

Round 1 converted his `:CTL_*` to our `:Control` model on the strength of his
*conceptual* endorsement — but Round 2 shows his code still actively builds on `:CTL_*`
(`modeler.py`, `L2_modeler.py`, `:CTL_ControlSatisfaction`, `L2_3.ttl`). We're now doing
the conversion **twice**, and it grows every round.

> **Recommendation: pause the merge and sync with the coworker to lock ONE vocabulary
> before more divergence.** This is the "loop him in" call deferred in Round 1; Round 2
> makes it the gating item. He endorsed `requires/capable/provides/protects` — the ask is
> to actually adopt the `:Control` *naming* in his code (or, if he prefers `:CTL_*`,
> decide that now and we adapt once). Either way, stop paying the conversion tax twice.

### Mergeable now, low risk, high value (vocab-independent)

- [ ] **Portable rdflib backend.** Genuinely useful for the demo (no GraphDB server).
      Two fixes make it work with our stack:
  1. Add **`RunUpdate`** to `rdflib_backend.py` (rdflib `graph.update(...)`) and delegate
     it from `graphdb.py` (`if _delegate: return _delegate.RunUpdate(update)`); our
     derivations + L3 `PropagateControlEvidence` need it.
  2. Switch its inference from `RDFS_Semantics` to **`OWLRL_Semantics`** so `owl:hasValue`
     fires (otherwise the archetype capable-tier is inert — the Step-3 issue, locally).
  - Then validate `runall.sh` on **both** backends (`backend = graphdb` and `rdflib`).
- [ ] **`modeler.py` shared `RenderThreats`** — adopt; our rendering already matches.

### Bigger reconciliation (after vocab is locked)

- [ ] **His L2 threat modeler + inbound/outbound role modeling** — fold in (convert its
      `:CTL_*`/`URI_TO_CONTROL` refs to our vocab). The inbound-vs-outbound modeling is
      threat-semantics worth reviewing on the threat-modeling side.
- [ ] **ControlSatisfaction bridge.** His hand-asserted `:CTL_ControlSatisfaction`
      answers the same question as our derived obligations + computed grading. Unify:
      either our grading **emits** satisfaction instances, or his L2 threat modeler
      **reads** our computed Mitigated/Open grade (and L3 IaC evidence) instead of
      hand-asserted links. This is the real payoff — one satisfaction model feeding both
      threat rendering and control grading.
- [ ] Carry over the **Round-1 P2 level-scoping** fix (scope `EvaluateSatisfaction` by
      level) — a prerequisite for the bridge, since both now read `:requiresControl`.

### Git mechanics (when we execute)

`git merge origin/master` into `vitaly-changes`. Expected touch-points: `graphdb.py`
(our `RunUpdate` + his delegate pattern → combine, add `RunUpdate` delegation),
`schema.ttl` (his `:CTL_ControlSatisfaction` → our vocab), `main.py` (his `-t` = L1+L2
threat vs our flag set), `L1_modeler.py`/`L1_3.ttl` (he re-touched in `:CTL_*`; we'd
re-convert). **No `L2_modeler.py` filename clash this time** — his is the threat modeler,
ours is `L2_control_modeler.py`.

## Guiding principle

The two efforts are **complementary, not competing**: his is the *threat* side (enumerate
STRIDE threats, flag each mitigated/open), ours is the *control* side (derive what's
required from policy, grade Open/Potential/Mitigated, confirm from IaC). The merge should
**keep both** and make them talk through one control vocabulary — not pick a winner.

---

## Decisions to lock first (with recommendations)

These ripple through everything, so settle them before touching code.

| # | Decision | Recommendation | Why |
|---|----------|----------------|-----|
| D1 | `:L2_API` vs `:L2_Interface` | **Adopt his `:L2_Interface`** | Mirrors `:L1_Interface` (consistent across levels), already committed; cost is a mechanical rename in *our* `L2_modeler.py` + `L3_extractor.py`. **[coworker]** owns this term. |
| D2 | Control vocabulary: his `:CTL_ControlSet` (`owl:OneOf`) vs our `:Control` class hierarchy | **CONFIRMED — base on our `:Control` model**, keep his **closed-set `allValuesFrom` guard** as a validation layer | Ours is the superset (scope + capable/provides/requires tiers + policies + archetypes + L3); his binary requires/provides is a special case of it. ✅ **coworker endorsed** the requires/capable/provides/protects model (2026-06-09). |
| D3 | Requires/provides property names | **CONFIRMED — our `:requiresControl` / `:capableOfControl` / `:providesControl`** (+ `:protects`); map his `:CTL_RequiresControls`→`:requiresControl`, `:CTL_ProvidesControls`→`:providesControl` | More granular; lowerCamel matches `:L2_invokesInterface` etc. ✅ **coworker endorsed**. |
| D4 | Control individuals & labels | **One set of individuals** (`:ClientAuthentication`…, not `:CTL_*`); pick labels: his `Data-in-transit`/`Data-at-rest Encryption` vs our `Traffic Encryption`/`Encryption at Rest` | Lean **his labels** (more standards-aligned, helps the future NIST/SKOS step) — but trivial to flip. Whatever wins, update `controls.py` to match (the enum-label sync invariant). |
| D5 | `L2_modeler.py` name clash | His stays **`L2_modeler.py`** (L2 *threat* modeler, paralleling `L1_modeler.py`); rename **ours → `L2_control_modeler.py`** | "modeler" already means "threat modeler" in their convention (`L1_modeler.py`); name ours for what it is. |
| D6 | `main.py` flags | **Keep his `-1`/`-2`** (per-level analyzers) + **our `-m`/`-x`/`-r`** + `-t` | Smallest churn to his committed CLI; our additions are orthogonal. |

---

## Phase 0 — Preserve our work (do this first)

Our work is uncommitted (incl. untracked files); the `L2_modeler.py` name clash means a
raw `git merge` would refuse to overwrite. So:

1. Branch off our base and commit our WIP **locally** (not pushed):
   `git switch -c vitaly-changes` (from current HEAD `3f83f93`), then
   `git add -A && git commit` our full working tree.
   - This is the first step that needs a "go" — it's a local branch only, addressing the
     earlier "don't commit yet" (nothing leaves the machine).
2. With our work safely on a commit, bring his in: `git merge origin/master`
   (or cherry-pick). Expect conflicts in every D1/D2 file — resolved per the decisions,
   not by git's auto-merge (the API/Interface rename won't auto-detect).

> Alternative if a 3-way merge gets too noisy: treat it as a **manual port** — start from
> his `origin/master` (so his committed history is the base) and re-apply our untracked
> additions (`L3_*.py`, `terraform/`, `docs/`) + re-derive our `schema.ttl`/`L2` edits
> onto his Interface naming. Often cleaner than fighting rename conflicts.

---

## Phase 1 — Mechanical reconciliation (apply the decisions)

1. **Naming (D1):** rename `:L2_API`→`:L2_Interface`, `:L2_invokesAPI`→`:L2_invokesInterface`,
   `:L2_exposesAPI`→`:L2_exposesInterface`, `:L2_API_to_L1`→`:L2_Interface_to_L1` in **our**
   `L2_modeler.py` (the derivation SPARQL), `L3_extractor.py`/`L3_analyzer.py` (they read
   `exposesAPI`/`invokesAPI`), and our L2 fixtures. (His side already uses Interface.)
2. **Control vocab (D2–D4):** one section in `schema.ttl` — our `:Control`/`:ChannelControl`/
   `:NodeControl` + individuals, our requires/capable/provides properties, plus his closed-set
   guard expressed over our set. Delete the `:CTL_*` duplicates. Update `controls.py` to the
   chosen labels. Re-point his `L1_3.ttl` and `L1_modeler.py` from `:CTL_RequiresControls`/
   `:CTL_*` to `:requiresControl`/`:ClientAuthentication`…
3. **File rename (D5):** `L2_modeler.py`(ours)→`L2_control_modeler.py`; fix the `main.py`
   import + the `-m` handler.
4. **Flags (D6):** single `argparse` block: `-c -s -d -1 -2 -t -m -x -r`. Update `runall.sh`
   to the merged sequence (load L1 + `L1_3` controls → `-1` → `-t`; load L2 → `-2` → `-m` →
   `-x` → `-r`).

**Checkpoint:** `tests/runall.sh` runs clean — his L1 threat modeler renders ✅/⚠️ **and**
our L2 control grading + L3 reconcile both work, on one schema.

---

## Phase 2 — Synergy (the actual payoff)

His threat modeler currently reads **hand-asserted** `:CTL_RequiresControls` (`L1_3.ttl`)
and flags binary mitigated/open. Wire it to our machinery:

1. **Requirements from policy, not by hand:** his "is control C required here?" reads the
   `:requiresControl` our derivation *computes* (zone-crossing / data-sensitivity), so
   `L1_3.ttl`'s manual assertions shrink or disappear.
2. **Mitigation from grading, not binary:** his per-threat icon consumes our
   Open/Potential/Mitigated grade (incl. **IaC-confirmed** via L3) instead of mere
   presence — so a threat can render 🟡 "potential" and ✅ "confirmed by Terraform".
3. **Extend to L2:** flesh out his `L2_modeler.py` (threat) stub to consume the same
   derived obligations at L2.

End state: one pipeline — derive requirements → grade with capability + IaC evidence →
render STRIDE threats as mitigated/potential/open, with conformance findings alongside.

---

## Phase 3 — Validate & document

- `runall.sh` green end-to-end; spot-check the headline cases (EncryptionAtRest
  OPEN→MITIGATED from IaC; a threat flipping ✅ once its derived control is provided).
- Fold this merge into `control-modeling.md` (a "Step 10 — merge") and refresh memory.
- Then (and only then) consider pushing the branch / opening a PR for the coworker.

---

## Sequencing summary

```
P0  preserve     → branch + commit our WIP, then merge his (or manual port)
P1  reconcile    → Interface naming · one control vocab · rename file · unify flags   [coworker sign-off on D1–D4]
P2  synergy      → his threat modeler consumes our derived obligations + IaC grade
P3  validate     → runall green · docs/memory · then PR
```

**Smallest first real step:** P0 (preserve) + the D1/D5 mechanical renames — low-risk,
unblocks everything, and needs no ontology decision. The control-vocab unification (D2–D4)
is the part to do **with the coworker**.
