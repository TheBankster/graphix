from graphdb import GetBindings, RunUpdate
from typing import List, Set, Tuple

### L3 Reconciliation: as-built (L3) vs intended (L1/L2) ###
#
# Two jobs (see docs/control-modeling.md, "Step 9"):
#   1. Evidence -- propagate the controls an L3 resource demonstrably provides across
#      its :L3_realizes link onto the L2 element, so the Step 7 satisfaction grading
#      runs on real IaC config instead of simulated triples.
#   2. Conformance -- flag where the as-built and the intended model disagree:
#        * shadow infrastructure: an L3 resource that realizes nothing modeled;
#        * unrealized model: an L2 component that nothing deployed realizes.

PREFIX = """
    PREFIX : <http://thefirm.com/graphix#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


# Stage 1: lift control evidence from each L3 element onto the L2 element it realizes.
# Idempotent (re-runnable).
def PropagateControlEvidence() -> None:
    update: str = PREFIX + """
        INSERT { ?l2 :providesControl ?control . }
        WHERE {
            ?l3 :L3_realizes ?l2 ;
                :providesControl ?control .
        }"""
    RunUpdate(update)


def _rows(query: str, *keys: str) -> List[Tuple[str, ...]]:
    bindings = GetBindings(PREFIX + query)
    out: List[Tuple[str, ...]] = []
    for b in bindings:
        out.append(tuple((b.get(k) or {}).get("value", "") for k in keys))
    return out


# As-built resources that realize nothing in the model = unmodeled / shadow infra.
def ShadowInfrastructure() -> List[Tuple[str, ...]]:
    return _rows("""
        SELECT ?label ?type WHERE {
            ?l3 a :L3_Element .
            FILTER NOT EXISTS { ?l3 :L3_realizes ?l2 . }
            OPTIONAL { ?l3 rdfs:label ?label . }
            OPTIONAL { ?l3 :L3_awsResourceType ?type . }
        } ORDER BY ?label""", "label", "type")


# Modeled components that nothing deployed realizes = intended-but-not-deployed.
# Actors are excluded: they are external entities, not deployable infrastructure.
# (Note: under OWL-RL an :L2_Actor that :L2_invokesAPI is also inferred an
# :L2_Container, because that property's domain is :L2_Container -- hence the
# explicit actor exclusion rather than relying on container typing alone.)
def UnrealizedModel() -> List[Tuple[str, ...]]:
    return _rows("""
        SELECT ?label WHERE {
            ?l2 a :L2_Container .
            FILTER NOT EXISTS { ?l2 a :L2_Actor . }
            FILTER NOT EXISTS { ?l3 :L3_realizes ?l2 . }
            OPTIONAL { ?l2 rdfs:label ?label . }
        } ORDER BY ?label""", "label")


# What each realized resource confirms, for the evidence report.
def ConfirmedEvidence() -> List[Tuple[str, ...]]:
    return _rows("""
        SELECT ?l3label ?l2label ?control WHERE {
            ?l3 :L3_realizes ?l2 ;
                :providesControl ?ctrl .
            ?ctrl rdfs:label ?control .
            OPTIONAL { ?l3 rdfs:label ?l3label . }
            OPTIONAL { ?l2 rdfs:label ?l2label . }
        } ORDER BY ?l2label ?control""", "l3label", "l2label", "control")


def L3_Reconciler() -> bool:
    print("🔭 Running L3 Reconciler (as-built vs intended)...")
    PropagateControlEvidence()

    evidence = ConfirmedEvidence()
    shadow = ShadowInfrastructure()
    unrealized = UnrealizedModel()

    if evidence:
        print("🔗 Control evidence confirmed from IaC:")
        for l3, l2, control in evidence:
            print(f"  ✅ {control} — {l2} (from {l3})")

    conformant = True
    if shadow:
        conformant = False
        print("👻 Deployed but NOT in the model (shadow infrastructure):")
        for label, rtype in shadow:
            print(f"  - {label} ({rtype})")

    if unrealized:
        conformant = False
        print("🚧 In the model but NOT deployed (unrealized):")
        for (label,) in unrealized:
            print(f"  - {label}")

    if conformant:
        print("🎈 L3 conformance: as-built matches the intended model")

    return conformant
