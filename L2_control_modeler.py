from graphdb import GetBindings, RunUpdate
from typing import List, Tuple

### L2 Control Modeling ###
#
# Two stages (see docs/control-modeling.md):
#   1. Derivation  -- materialize :requiresControl obligations from the
#      boundary-crossing policy: walk each call edge, read the caller/callee zone
#      types, match a :BoundaryCrossingPolicy, and assert the controls it mandates
#      on the exposed interface. (Channel controls only; node-control obligations such as
#      encryption-at-rest derive from data sensitivity and are asserted separately.)
#   2. Satisfaction -- grade each obligation Open / Potential / Mitigated, branching
#      on control scope:
#        * ChannelControl: satisfied by a protector that :protects the element and
#          :providesControl (Mitigated) / only :capableOfControl (Potential) it.
#        * NodeControl: satisfied by the element providing the control on itself.

PREFIX = """
    PREFIX : <http://thefirm.com/graphix#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# Stage 1: derive channel-control obligations from the boundary-crossing policy and
# assert them as :requiresControl on the exposed interface. Idempotent (re-runnable).
def DeriveChannelObligations() -> None:
    update: str = PREFIX + """
        INSERT { ?interface :requiresControl ?control . }
        WHERE {
            # the call edge: caller invokes an interface that callee exposes
            ?caller :L2_invokesInterface ?interface .
            ?callee :L2_exposesInterface ?interface .
            ?callee :L2_insideTrustBoundary ?calleeZone .
            ?calleeZone a ?toType .

            # caller's zone type: a container sits in a zone; an external actor is
            # treated as originating in the Untrusted zone.
            { ?caller :L2_insideTrustBoundary ?callerZone . ?callerZone a ?fromType . }
            UNION
            { ?caller a :L2_Actor . BIND(:UntrustedZone AS ?fromType) }

            # match a boundary-crossing policy on the (fromType, toType) pair
            ?policy a :BoundaryCrossingPolicy ;
                    :crossingFromType ?fromType ;
                    :crossingToType   ?toType ;
                    :mandatesControl  ?control .
        }"""
    RunUpdate(update)

# Stage 1b: derive node-control obligations from data sensitivity. A node that handles
# data of a given sensitivity inherits the controls its :DataProtectionPolicy mandates,
# asserted as :requiresControl on the node itself. Idempotent (re-runnable).
def DeriveNodeObligations() -> None:
    update: str = PREFIX + """
        INSERT { ?node :requiresControl ?control . }
        WHERE {
            ?node :handlesDataOfSensitivity ?sensitivity .
            ?policy a :DataProtectionPolicy ;
                    :appliesToSensitivity ?sensitivity ;
                    :mandatesControl      ?control .
        }"""
    RunUpdate(update)

# Stage 2: resolve every :requiresControl obligation to a satisfaction state.
# Returns tuples of (element URI, element label, control label, scope, state).
def EvaluateSatisfaction() -> List[Tuple[str, str, str, str, str]]:
    query: str = PREFIX + """
        SELECT ?element ?elementLabel ?control ?scope ?state
        WHERE {
            ?element :requiresControl ?ctrl .
            ?ctrl rdfs:label ?control .
            OPTIONAL { ?element rdfs:label ?elementLabel . }

            BIND( IF(EXISTS { ?ctrl a :NodeControl }, "node", "channel") AS ?scope )
            BIND(
                IF(?scope = "node",
                    # node control: the element must provide it on itself
                    IF(EXISTS { ?element :providesControl ?ctrl }, "MITIGATED",
                       IF(EXISTS { ?element :capableOfControl ?ctrl }, "POTENTIAL", "OPEN")),
                    # channel control: satisfied by a protector on the path
                    IF(EXISTS { ?p :protects ?element ; :providesControl ?ctrl }, "MITIGATED",
                       IF(EXISTS { ?p :protects ?element ; :capableOfControl ?ctrl }, "POTENTIAL", "OPEN"))
                ) AS ?state )
        }
        ORDER BY ?elementLabel ?control"""
    bindings = GetBindings(query)
    results: List[Tuple[str, str, str, str, str]] = []

    for result in bindings:
        def val(key: str) -> str:
            binding = result.get(key)
            return binding["value"] if binding else ""

        results.append((val("element"), val("elementLabel"), val("control"), val("scope"), val("state")))

    return results

_STATE_ICON = {"MITIGATED": "✅", "POTENTIAL": "🟡", "OPEN": "🛑"}

def RenderSatisfaction(results: List[Tuple[str, str, str, str, str]]) -> None:
    print("📋 Control satisfaction:")
    if not results:
        print("  (no control obligations derived)")
        return
    for element, label, control, scope, state in results:
        icon = _STATE_ICON.get(state, "•")
        name = label if label else element
        print(f"  {icon} {state:<9} {control} ({scope}) — {name}")

def L2_ControlModeler() -> List[Tuple[str, str, str, str, str]]:
    print("🧮 Running L2 Control Modeler...")
    DeriveChannelObligations()
    DeriveNodeObligations()
    results = EvaluateSatisfaction()
    RenderSatisfaction(results)
    return results
