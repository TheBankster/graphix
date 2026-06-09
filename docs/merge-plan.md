# Reconciliation / merge plan — our work + coworker's `origin/master`

Companion to [coworker-comparison.md](coworker-comparison.md). Goal: land both bodies of
work on one branch with a single shared vocabulary, then exploit the synergy (his
mitigation-aware threat modeler consuming our derived obligations + IaC evidence).

Nothing here is executed yet. Schema/ontology decisions are marked **[coworker]** — they
own the ontology, so those need their sign-off (the rest is our threat-modeling side).

---

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
   `git switch -c merge-coworker` (from current HEAD `3f83f93`), then
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
