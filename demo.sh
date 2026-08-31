#!/bin/bash
# Babel — full-pipeline demo (L1 → L2 → L3), ~5 min. Self-narrating; the
# longer-form talk track in docs/demo.md covers the same arc in more detail.
# Runs against the backend set in graphix.config (default: GraphDB).
#
# Usage:
#   ./demo.sh              paced walkthrough; Enter advances between steps
#   ./demo.sh --no-pause   run start to finish without stopping
#   ./demo.sh --from 7     replay steps 1-6 silently, then present from step 7
#   ./demo.sh --list       print the step list and exit
#
# The framing, the rollups and the before/after panel are computed here in the
# script; the graph results themselves are the engine's own, indented under the
# command that produced them. Presentation-only edits: the repeated connection
# preamble is dropped after step 1; the graphix# namespace prefix is stripped
# off URIs; and the threat modeler's five-line-per-threat blocks are condensed
# to one line each (dropping the "mitigating entity" column) so a full threat
# set fits on screen. Run `python3 main.py -t` directly for the unabridged form.

cd "$(dirname "$0")"

PY="${PYTHON:-}"
if [[ -z $PY ]]; then
  PY="python3"
  [[ -x .venv/bin/python3 ]] && PY=".venv/bin/python3"
fi

PAUSE=1
FROM=1
TOTAL=9

# ── colours ───────────────────────────────────────────────────────────────────
if [[ -t 1 && -z ${NO_COLOR:-} ]]; then
  B=$'\033[1m'; D=$'\033[2m'; R=$'\033[0m'
  RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'
  BLU=$'\033[34m'; MAG=$'\033[35m'; CYN=$'\033[36m'
  L1C=$'\033[1;44m'; L2C=$'\033[1;45m'; L3C=$'\033[1;46m'; SETC=$'\033[1;100m'
else
  B=; D=; R=; RED=; GRN=; YLW=; BLU=; MAG=; CYN=; L1C=; L2C=; L3C=; SETC=
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── step plumbing ─────────────────────────────────────────────────────────────
STEP=0
STEP_TITLES=(
  "Reset the graph and load the ontology"
  "Load the L1 context model"
  "Derive threats from the topology alone"
  "Declare the controls the interfaces require"
  "Load the L2 containers and trust zones"
  "Derive control obligations and grade them"
  "Extract the as-built layer from real Terraform"
  "Reconcile against as-built, and re-grade"
  "So what"
)

active() { [[ $STEP -ge $FROM ]]; }

rule()  { printf '%s%s%s\n' "$D" "$(printf '─%.0s' $(seq 1 78))" "$R"; }
heavy() { printf '%s%s%s\n' "$B" "$(printf '═%.0s' $(seq 1 78))" "$R"; }

# badge <level>
badge() {
  case $1 in
    L1)    printf '%s L1 %s' "$L1C" "$R" ;;
    L2)    printf '%s L2 %s' "$L2C" "$R" ;;
    L3)    printf '%s L3 %s' "$L3C" "$R" ;;
    RECAP) printf '%s RECAP %s' "$SETC" "$R" ;;
    *)     printf '%s SETUP %s' "$SETC" "$R" ;;
  esac
}

# step <level> <why…> — prints the header, then waits
# Sets the title from STEP_TITLES so the list and the headers can't drift apart.
step() {
  local level=$1; shift
  STEP=$((STEP + 1))
  if ! active; then
    printf '%s  ⏩ replaying step %d/%d — %s%s\n' \
      "$D" "$STEP" "$TOTAL" "${STEP_TITLES[$((STEP - 1))]}" "$R"
    return
  fi
  # PRE_PAUSE moves the wait to before the header and clears the screen, for a
  # step that wants a fresh screen rather than to open under the previous one.
  if [[ ${PRE_PAUSE:-0} == 1 && $PAUSE == 1 ]]; then
    echo
    printf '  %s[Enter to continue]%s ' "$B" "$R"; read -r
    clear 2>/dev/null
  fi
  echo
  heavy
  printf ' %s  %s[%d/%d]%s  %s%s%s\n' \
    "$(badge "$level")" "$D" "$STEP" "$TOTAL" "$R" "$B" "${STEP_TITLES[$((STEP - 1))]}" "$R"
  heavy
  local tag
  for tag in "$@"; do
    case $tag in
      WHY:*)   printf '  %sWHY  %s %s\n' "$CYN" "$R" "${tag#WHY:}" ;;
      LOAD:*)  printf '  %sLOAD %s %s\n' "$MAG" "$R" "${tag#LOAD:}" ;;
      WATCH:*) printf '  %sWATCH%s %s\n' "$YLW" "$R" "${tag#WATCH:}" ;;
      *)       printf '        %s\n' "$tag" ;;
    esac
  done
  # One pause per step, here — so the explanation and everything it runs land
  # together rather than the step being interrupted between its commands.
  if [[ $PAUSE == 1 && ${PRE_PAUSE:-0} != 1 ]]; then
    echo
    printf '  %s[Enter to run]%s ' "$B" "$R"; read -r
  fi
}

# Cosmetic filter for engine output (see header comment).
polish() {
  local drop='/^🛠️ Tracing is:/d; /^📡 StartGraphClients:/d'
  [[ ${KEEP_PREAMBLE:-0} == 1 ]] && drop=''
  sed -e "$drop" -e 's|http://thefirm\.com/graphix#||g' -e 's/^/    /'
}

# Condense the threat modeler's five-line blocks to one line per threat, grouped
# under their STRIDE category. Same data minus the mitigating-entity column.
compact_threats() {
  sed 's|http://thefirm\.com/graphix#||g' |
  awk -v grn="$GRN" -v red="$RED" -v b="$B" -v d="$D" -v r="$R" '
    /^##### / { printf "    %s%s threat modeler%s\n", d, $2, r; next }
    / Threat Category: / {
      icon = $1
      cat = $0; sub(/.* Threat Category: /, "", cat)
      printf "      %s %s%s%s\n", icon, b, cat, r
      next
    }
    /Attacker node:/    { attacker = $3; next }
    /Vulnerable node:/  { victim = $3; next }
    /Mitigating control:/ {
      mark = $NF
      control = ""
      for (i = 3; i < NF; i++) control = control (i > 3 ? " " : "") $i
      printf "         %s %s%-22s%s %s → %s\n",
        mark, (mark == "✅" ? grn : red), control, r, attacker, victim
    }'
}

# go [--capture FILE] <args to main.py…>
go() {
  local cap="$TMP/last.out"
  [[ $1 == --capture ]] && { cap=$2; shift 2; }
  if active; then
    echo
    printf '  %s$ python3 main.py %s%s\n' "$D" "$*" "$R"
    "$PY" main.py "$@" 2>&1 | tee "$cap" | "${FILTER:-polish}"
  else
    "$PY" main.py "$@" > "$cap" 2>&1
  fi
}

# Beat: a "so what" callout after a result. beat <colour> <headline> <line…>
beat() {
  active || return 0
  local col=$1 head=$2; shift 2
  echo
  printf '  %s%s▐%s %s%s%s\n' "$col" "$B" "$R" "$B" "$head" "$R"
  local l
  for l in "$@"; do printf '  %s%s▐%s %s\n' "$col" "$B" "$R" "$l"; done
}

# ── panels ────────────────────────────────────────────────────────────────────

# Count mitigated/open per threat-modeler section.
threat_rollup() {
  active || return 0
  echo
  awk -v grn="$GRN" -v red="$RED" -v b="$B" -v d="$D" -v r="$R" '
    /^##### / {
      sec = $2
      if (!(sec in seen)) { seen[sec] = 1; order[++n] = sec }
      ok[sec] += 0; bad[sec] += 0
      next
    }
    /Mitigating control:/ {
      if (index($0, "✅")) ok[sec]++; else bad[sec]++
    }
    END {
      printf "  %sTHREAT ROLLUP%s\n", b, r
      for (i = 1; i <= n; i++) {
        s = order[i]; total = ok[s] + bad[s]
        if (total == 0) {
          printf "    %s%s%s  %s(nothing derived at this level yet)%s\n", b, s, r, d, r
          continue
        }
        printf "    %s%s%s  %s✅ %d mitigated%s   %s%s %d open%s   %s(%d threats)%s\n",
          b, s, r, grn, ok[s], r, (bad[s] ? red : d), (bad[s] ? "🛑" : "•"), bad[s], r, d, total, r
      }
    }' "$1"
}

# Normalise `  🛑 OPEN      Control (scope) — Element` into `STATE|Control — Element`.
sat_rows() {
  sed -n 's/^  [^ ]* \([A-Z]*\) *\(.*\) (\(node\|channel\)) — \(.*\)$/\1|\2 — \4/p' "$1"
}

# Side-by-side diff of two control-satisfaction runs.
sat_diff() {
  active || return 0
  sat_rows "$1" > "$TMP/before.rows"
  sat_rows "$2" > "$TMP/after.rows"
  echo
  awk -F'|' -v grn="$GRN" -v red="$RED" -v ylw="$YLW" -v b="$B" -v d="$D" -v r="$R" '
    function icon(s) { return s == "MITIGATED" ? "✅" : (s == "POTENTIAL" ? "🟡" : "🛑") }
    function col(s)  { return s == "MITIGATED" ? grn : (s == "POTENTIAL" ? ylw : red) }
    function cell(s) { return sprintf("%s%s %-9s%s", col(s), icon(s), s, r) }
    NR == FNR { before[$2] = $1; next }
    # 5-space gutter + 15-wide field lands the headings over the state words,
    # which sit 3 columns into each cell behind a double-width emoji.
    FNR == 1 { printf "    %s%-30s     %-15s%s%s\n", d, "OBLIGATION", "intended", "as-built", r }
    {
      key = $2; now = $1; was = before[key]
      split(key, part, " — ")
      mark = ""
      if (was != now) { mark = sprintf("  %s%s← flipped%s", grn, b, r); flipped++ }
      printf "    %s%-30s%s  %s → %s%s\n", b, part[1], r, cell(was), cell(now), mark
      printf "      %son %s%s\n", d, part[2], r
    }
    END {
      printf "\n    %s%d of %d obligations changed state on evidence from Terraform.%s\n", d, flipped, FNR, r
    }
  ' "$TMP/before.rows" "$TMP/after.rows"
}

# Pull the shadow-infrastructure block out of the reconcile output.
shadow_panel() {
  active || return 0
  local list
  list=$(awk '/^👻 /{grab=1; next} grab && /^  - /{print; next} grab{exit}' "$1")
  [[ -z $list ]] && return 0
  echo
  printf '  %s%s┌─ SHADOW IT ─────────────────────────────────────────────────┐%s\n' "$RED" "$B" "$R"
  while IFS= read -r l; do
    printf '  %s%s│%s  %s%s%s\n' "$RED" "$B" "$R" "$B" "${l#  - }" "$R"
  done <<< "$list"
  printf '  %s%s│%s  %sIn the Terraform plan. Absent from the threat model.%s\n' "$RED" "$B" "$R" "$D" "$R"
  printf '  %s%s└─────────────────────────────────────────────────────────────┘%s\n' "$RED" "$B" "$R"
}

# ── arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --no-pause) PAUSE=0; shift ;;
    --from)     FROM=$2; shift 2 ;;
    --list)
      echo "Babel demo steps:"
      for i in "${!STEP_TITLES[@]}"; do printf '  %d. %s\n' "$((i + 1))" "${STEP_TITLES[$i]}"; done
      exit 0 ;;
    # The header comment block, minus the shebang, is the help text.
    -h|--help) awk 'NR > 1 && /^#/ { print; next } NR > 1 { exit }' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── title card ────────────────────────────────────────────────────────────────
clear 2>/dev/null
echo
heavy
printf ' %sBABEL%s — architecture as a graph, security as a query over it\n' "$B" "$R"
heavy
echo
echo "  Three levels of the same system, each loaded as RDF into one graph:"
echo
# 4 spaces + 4-wide badge + 2 = text starts at column 10; wraps align at 22.
level_line() { printf '    %s  %s%-11s%s%s\n' "$(badge "$1")" "$B" "$2" "$R" "$3"; }
wrap_line()  { printf '                     %s\n' "$1"; }
level_line L1 "Context"    "systems, external actors, the interfaces"
wrap_line "between them, and the perimeter around what we own"
level_line L2 "Containers" "what is inside each system — services, data"
wrap_line "stores, gateways — and the trust zones they sit in"
level_line L3 "As-built"   "what is ${B}actually deployed${R} — extracted from"
wrap_line "Terraform rather than modelled by hand"
cat <<EOF

  ${CYN}What this run shows:${R} L1 and L2 are modelled, L3 is read from Terraform.
  Everything else on screen — threats, control obligations, their state, and
  the gap between model and deployment — is ${B}derived${R} from those three inputs.

EOF
if [[ $FROM -gt 1 ]]; then
  printf '  %sReplaying steps 1-%d silently, presenting from step %d.%s\n\n' "$D" "$((FROM - 1))" "$FROM" "$R"
fi
if [[ $PAUSE == 1 ]]; then
  printf '  %s[Enter to begin]%s ' "$B" "$R"; read -r
fi

# ═══ 1 ════════════════════════════════════════════════════════════════════════
step SETUP \
  "WHY:The ontology is the rulebook: what a trust zone is, what controls exist," \
  "and which boundary crossings mandate which controls. It carries no system." \
  "LOAD:schema.ttl — classes, properties, and the boundary-crossing policies"
KEEP_PREAMBLE=1 go -c
KEEP_PREAMBLE=1 go -s schema.ttl

# ═══ 2 ════════════════════════════════════════════════════════════════════════
step L1 \
  "WHY:The L1 model is small and boring on purpose: who talks to whom." \
  "No threats, no controls, no security content of any kind — just topology." \
  "LOAD:tests/L1_1.ttl  an e-commerce platform, its customer, a payment" \
  "                 gateway and a notification service" \
  "LOAD:tests/L1_2.ttl  three edges the first file deliberately left out"
go -d tests/L1_1.ttl
go -d tests/L1_2.ttl

# ═══ 3 ════════════════════════════════════════════════════════════════════════
step L1 \
  "WHY:The threat modeler walks each actor → interface → system path and emits" \
  "the STRIDE threats that shape implies: an external actor reaching an" \
  "internal system means spoofing, disclosure, denial of service, elevation." \
  "WATCH:Eight threats, all 🛑 open — the graph holds topology and nothing else."
FILTER=compact_threats go --capture "$TMP/t1.out" -t
threat_rollup "$TMP/t1.out"

# ═══ 4 ════════════════════════════════════════════════════════════════════════
step L1 \
  "WHY:L1_3 is the one file a person writes by hand: what each interface is" \
  "required to provide. It records intent, not that anything provides it." \
  "LOAD:tests/L1_3.ttl — client auth, traffic encryption, rate limiting," \
  "                 access control" \
  "WATCH:Nothing is graded here. These obligations get resolved one level down."
go -d tests/L1_3.ttl

# ═══ 5 ════════════════════════════════════════════════════════════════════════
step L2 \
  "WHY:Drop a level. Containers, the trust zone each one sits in, and the" \
  "sensitivity of the data they hold." \
  "LOAD:tests/L2_1.ttl — web front-end, processing engine, product database," \
  "                 an edge API gateway, and two trust zones"
go -d tests/L2_1.ttl

# ═══ 6 ════════════════════════════════════════════════════════════════════════
step L2 \
  "WHY:For each call edge the control modeler reads the trust zone at both" \
  "ends, matches a boundary-crossing policy in the ontology, and asserts the" \
  "controls that crossing mandates. Node controls derive the same way, from" \
  "the sensitivity of the data an element handles." \
  "WATCH:Five obligations, none of them typed by hand, and the state of each."
go --capture "$TMP/m_before.out" -m
beat "$MAG" "Where 'Encryption at Rest' came from:" \
  "the database :handlesDataOfSensitivity :Confidential → the data-protection" \
  "policy for Confidential mandates encryption at rest → obligation asserted." \
  "Nothing provides it, so it grades 🛑 OPEN. The gateway is an API gateway, so" \
  "it is :capableOfControl client auth and TLS — capability only, hence 🟡." \
  "" \
  "That is the gap state of the ${B}intended${R} model. Next: what is actually deployed."

# ═══ 7 ════════════════════════════════════════════════════════════════════════
step L3 \
  "WHY:The extractor runs terraform plan, reads the JSON, and turns each" \
  "significant resource into an L3 element. A graphix_l2 tag says which model" \
  "element it realizes; config attributes become control evidence — a volume" \
  "with storage_encrypted = true provides encryption at rest." \
  "LOAD:terraform/ — a real AWS stack: VPC, ALB, ECS, RDS, API Gateway" \
  "WATCH:Five resources extracted. terraform init and plan take a few seconds."
go -x terraform

# ═══ 8 ════════════════════════════════════════════════════════════════════════
step L3 \
  "WHY:Reconcile the two. Every deployed resource is matched to the model" \
  "element it realizes, and its proven controls are lifted onto that element." \
  "Then re-run the exact same grading as step 6 — same policy, same query." \
  "The only thing that changed is that the graph has now read the Terraform." \
  "WATCH:Which obligations move, which do not — and what matched nothing at all."
go --capture "$TMP/recon.out" -r
go --capture "$TMP/m_after.out" -m
sat_diff "$TMP/m_before.out" "$TMP/m_after.out"
beat "$GRN" "Both flips trace to a line of Terraform:" \
  "encryption at rest ← ${B}storage_encrypted = true${R} on the RDS instance;" \
  "traffic encryption ← the API gateway's managed endpoint serves TLS." \
  "" \
  "The two that held still are unmet for equally concrete reasons: no" \
  "authorizer is attached to the API gateway, so client auth stays 🟡 —" \
  "capable, unconfirmed. Nothing in the stack shows access control on the DB."
shadow_panel "$TMP/recon.out"
beat "$RED" "How the load balancer surfaced:" \
  "it carries no graphix_l2 tag, so it realizes no model element, so the" \
  "conformance query returns it. Same query, same pass that confirmed the" \
  "two controls above — one direction finds evidence, the other finds drift." \
  "" \
  "It sits in the production request path in front of the web tier, and every" \
  "threat it introduces is currently unassessed."

# ═══ 9 ════════════════════════════════════════════════════════════════════════
# Its own step so the recap gets a clear screen instead of scrolling off the
# top behind the step-8 output.
PRE_PAUSE=1 step RECAP
cat <<EOF

  Four outputs, and where each one came from:

    ${GRN}✓${R}  ${B}STRIDE threats${R}        the call topology alone (step 3)
    ${GRN}✓${R}  ${B}Control obligations${R}   trust-zone crossings and data
                             sensitivity, via ontology policy (step 6)
    ${GRN}✓${R}  ${B}Control state${R}         attributes in the Terraform plan (step 8)
    ${GRN}✓${R}  ${B}Shadow infrastructure${R} resources realizing no model element,
                             from the same pass (step 8)

  ${CYN}The hand-written inputs were the L1/L2 model and one requirements file.${R}
  Re-running against a changed Terraform re-grades all of it.

EOF
printf ' %sTry:%s ./demo.sh --from 7   %sreplays the setup and opens on the L3 payoff%s\n\n' "$D" "$R" "$D" "$R"
