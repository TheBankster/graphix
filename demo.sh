#!/bin/bash
# GRAPHIX — L3 (as-built / IaC) demo, ~3 min. Talk track: docs/demo.md
# Runs against the backend set in graphix.config (default: GraphDB).
# Press Enter to advance between steps so you can talk over each one.

cd "$(dirname "$0")"

step() {
  echo
  echo "────────────────────────────────────────────────────────"
  echo "▶ $1"
  read -r -p "   [Enter to run] "
  echo
}

step "Reset + load the ontology and the intended L1 model"
python3 main.py -c
python3 main.py -s schema.ttl
python3 main.py -d tests/L1_1.ttl
python3 main.py -d tests/L1_2.ttl
python3 main.py -d tests/L1_3.ttl

step "Add the L2 detail: containers, interfaces, trust zones"
python3 main.py -d tests/L2_1.ttl

step "Control modeler — derive required controls from policy + grade (THE GAPS)"
python3 main.py -m

step "Extract the AS-BUILT layer from real Terraform"
python3 main.py -x terraform

step "Reconcile as-built vs intended — confirm from config + flag shadow infra"
python3 main.py -r

step "Re-grade — now with REAL IaC evidence (gaps flip to MITIGATED)"
python3 main.py -m

echo
echo "✅ Demo complete."
