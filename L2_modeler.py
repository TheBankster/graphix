from graphdb import GetBindings
from stride import STRIDE
from controls import CONTROL
from typing import Set, Tuple, FrozenSet, Dict
from collections import defaultdict
from modeler import RenderThreats, CONTROL_TO_STRIDE, URI_TO_CONTROL

### L2 Threat Modeling Rules ###

# Each Threat Model analysis returns a set of tuples, each containing:
#   - STRIDE threat (from the list above)
#   - Tuple of graph node URIs and controls employed for mitigations:
#       - Attacker URI 
#       - Vulnerable Party URI
#       - URI of the entity employing the control
#       - Control type

# All L1 control requirements must be satisfied by L2 elements; the ones that aren't need to be flagged
def L2_Controls_L1_Requirements() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]:
    """
    Identifies L2 elements that satisfy L1 control requirements by tracing 
    the L1 interaction paths to identify actual attackers and vulnerable nodes.
    """
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        SELECT ?attacker ?vulnerable ?l1_requirement_node ?required_control ?l2_element
        WHERE {
            ?l1_requirement_node a :L1_Element .
            ?l1_requirement_node :CTL_RequiresControls ?required_control .

            {
                # Case 1: Requirement is on an Interface
                ?l1_requirement_node a :L1_Interface .
                ?vulnerable :L1_exposesInterface ?l1_requirement_node .
                ?attacker :L1_invokesInterface ?l1_requirement_node .
            }
            UNION
            {
                # Case 2: Requirement is on a Software System
                ?l1_requirement_node a :L1_SoftwareSystem .
                BIND(?l1_requirement_node AS ?vulnerable)
                ?vulnerable :L1_exposesInterface ?iface .
                ?attacker :L1_invokesInterface ?iface .
            }

            OPTIONAL {
                ?satisfaction a :CTL_ControlSatisfaction ;
                              :CTL_satisfiesRequirementOf ?l1_requirement_node ;
                              :CTL_satisfiedControl ?required_control ;
                              :CTL_isSatisfiedBy ?l2_element .
                ?l2_element a :L2_Element .
            }
        }"""
    
    bindings = GetBindings(query)
    threat_groups = defaultdict(list)

    for result in bindings:
        attacker_uri = result.get("attacker", {}).get("value", "")
        vulnerable_uri = result.get("vulnerable", {}).get("value", "")
        control_uri = result.get("required_control", {}).get("value", "")
        l2_uri = result.get("l2_element", {}).get("value", "")
        
        # Extract control local name (e.g., CTL_ClientAuthentication) from URI
        control_fragment = control_uri.split("#")[-1]
        control_enum = URI_TO_CONTROL.get(control_fragment)
        
        if not control_enum:
            continue
            
        stride_threat = CONTROL_TO_STRIDE.get(control_enum, STRIDE.TAMPERING)
        is_satisfied = bool(l2_uri)
        mitigating_entity = l2_uri if is_satisfied else "UNSATISFIED"
        
        # Output format: (Attacker, Vulnerable, Mitigator, Control, Status)
        threat_groups[stride_threat].append((attacker_uri, vulnerable_uri, mitigating_entity, control_enum, is_satisfied))

    # Group entries into the standard Result set format
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]] = {
        (threat, frozenset(entries)) for threat, entries in threat_groups.items()
    }
    
    return results

def L2_ThreatModeler() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]:
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]] = set()
    
    # Accumulate all threats from different architectural bounds
    results.update(L2_Controls_L1_Requirements())
    
    # Sort the results by the first element of the tuple (STRIDE enum value)
    # This groups all SPOOFING together, all DENIAL_OF_SERVICE together, etc.
    grouped_results = sorted(results, key=lambda x: x[0].value)
    
    print("\n##### L2 Threat Modeler Results #####")
    # Pass the ordered list to the renderer so they print out cleanly grouped
    RenderThreats(grouped_results)
    
    return results
