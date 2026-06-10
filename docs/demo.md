# GRAPHIX demo — talk track

Run from the repo root. Each block has the command(s) and a line to say. The arc:
**intended model → threats → control gaps → confirm against real IaC.**

> One-liner to open with: *"GRAPHIX is a semantic threat-modeling engine — you model the
> intended architecture once, it derives the required security controls, and then reads
> your real Terraform to tell you which controls are actually in place and what got
> deployed that you never modeled."*

---

## 0. Load the model (setup)

```bash
python3 main.py -c                   # clear the graph
python3 main.py -s schema.ttl        # load the ontology (the rules of the world)
python3 main.py -d tests/L1_1.ttl    # L1 context: systems, actors, interfaces
python3 main.py -d tests/L1_2.ttl
python3 main.py -d tests/L1_3.ttl    # L1 control *requirements* (what each interface needs)
```

> *"We load the ontology, then the Level-1 architecture — the big-picture systems and the
> security controls each interface requires."*

---

## 1. Threats

```bash
python3 main.py -1                   # L1 semantic analyzer — structural sanity check
python3 main.py -t                   # threat modeler — STRIDE threats, mitigated vs open
```

> *"First it validates the model is well-formed. Then the threat modeler enumerates STRIDE
> threats per interaction and marks each ✅ mitigated or ⚠️ open, based on whether the
> required control is present. This is the threat-modeling output a security engineer
> would normally hand-build."*

---

## 2. Control modeling — the gap state

```bash
python3 main.py -d tests/L2_1.ttl    # L2 detail: containers, interfaces, trust zones
python3 main.py -2                   # L2 semantic analyzer
python3 main.py -m                   # control modeler: derive obligations + grade
```

> *"At Level 2 we add the containers and trust zones. The control modeler doesn't take a
> checklist — it **derives** the required controls from policy: crossing from the public
> internet into the web tier mandates encryption + auth; a database holding confidential
> data mandates encryption-at-rest. Then it grades each: ✅ Mitigated, 🟡 Potential (the
> component could do it but isn't confirmed), 🛑 Open."*

**Point at:** `Encryption at Rest 🛑 OPEN`, `Traffic Encryption 🟡 POTENTIAL`.
> *"These are the gaps in the intended model. Now — are they real?"*

---

## 3. The IaC bridge — confirm against reality

```bash
python3 main.py -x terraform         # extract the AS-BUILT layer from real Terraform
python3 main.py -r                   # reconcile as-built vs intended
python3 main.py -m                   # re-grade, now with REAL evidence
```

> *"`-x` runs the actual Terraform and extracts every deployed resource as an 'as-built'
> layer, linked to the model. `-r` reconciles the two."*

**Point at the reconcile output:**
- `✅ Encryption at Rest — from webapp-prod-postgres` → *"the real RDS instance is encrypted, so that's confirmed from config, not assumed."*
- `✅ Traffic Encryption — from the API gateway` → *"the managed endpoint serves TLS."*
- `👻 webapp-prod-alb — deployed but NOT in the model` → *"and it caught a load balancer in the request path that the threat model never knew about — shadow infrastructure."*

**Point at the final `-m`:** `Encryption at Rest` and `Traffic Encryption` flip 🛑/🟡 → ✅ **MITIGATED**.
> *"The gaps that were open are now confirmed mitigated — from real config. And the ones
> still open are genuinely open: the IaC shows no authorizer, so Client Auth stays a gap.
> Nothing hand-waved."*

---

## 4. (Optional) Runs with no server

> *"All of that ran on GraphDB. Flip one config line — `backend = \"rdflib\"` — and the
> exact same pipeline runs in-process with no database server at all. Same results."*

```bash
# edit graphix.config: backend = "rdflib"   then re-run any of the above
```

---

## The whole thing at once

```bash
cd tests && bash runall.sh           # full pipeline end-to-end (incl. L2 threat modeler + extras)
```

## 30-second closer

> *"So: model the intended design once → it derives the controls and the threats → it
> reads your real infrastructure and tells you what's actually mitigated, what's only
> potential, and what's deployed but unmodeled. Threat modeling that stays honest against
> what's really running."*
