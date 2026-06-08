from graphdb import GetBindings
from stride import STRIDE
from controls import CONTROL
from typing import Set, Tuple, FrozenSet

### L1 Threat Modeling Rules ###

# Each Threat Model analysis returns a set of tuples, each containing:
#   - STRIDE threat (from the list above)
#   - Tuple of graph node URIs and controls employed for mitigations:
#       - Attacker URI 
#       - Vulnerable Party URI
#       - URI of the entity employing the control
#       - Control type

# External actors invoking internal systems present these threats:
#   - Spoofing (mitigated by Authentication at the corresponding Interface)
#   - Elevation of Privilege (mitigated by Access Control by the Internal System)
#   - Information Disclosure (mitigated by Traffic Encryption by the corresponding Interface)
#   - Denial of Service (mitigated by Rate Limiting by the corresponding Interface)
def ExternalActorInternalSystem() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?actor ?interface ?system
        WHERE {
            ?actor a :L1_Actor .
            ?interface a :L1_Interface .
            ?system a :L1_InternalSystem .
            ?actor :L1_invokesInterface ?interface .
            ?system :L1_exposesInterface ?interface .
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]] = set()

    for result in bindings:
        actor_uri_binding = result.get("actor")
        interface_uri_binding = result.get("interface")
        system_uri_binding = result.get("system")

        actor_uri = actor_uri_binding["value"] if actor_uri_binding else ""
        interface_uri = interface_uri_binding["value"] if interface_uri_binding else ""
        system_uri = system_uri_binding["value"] if system_uri_binding else ""

        results.add((STRIDE.SPOOFING, frozenset([(actor_uri, system_uri, interface_uri, CONTROL.CLIENT_AUTHENTICATION)])))
        results.add((STRIDE.DENIAL_OF_SERVICE, frozenset([(actor_uri, system_uri, interface_uri, CONTROL.RATE_LIMITING)])))
        results.add((STRIDE.ELEVATION_OF_PRIVILEGE, frozenset([(actor_uri, system_uri, system_uri, CONTROL.ACCESS_CONTROL)])))
        results.add((STRIDE.INFORMATION_DISCLOSURE, frozenset([(actor_uri, system_uri, interface_uri, CONTROL.TRAFFIC_ENCRYPTION)])))
    return results

# Internal systems exposing external systems present these threats:
#   - Spoofing of the External Service, mitigated by Server Authentication by the Internal Service
#   - Information disclosure, mitigated by Traffic Encryption by the External Services' Interface
def InternalSystemExternalSystem() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?internalSystem ?externalSystem
        WHERE {
            ?internalSystem a :L1_InternalSystem .
            ?interface a :L1_Interface .
            ?externalSystem a :L1_ExternalSystem .
            ?internalSystem :L1_invokesInterface ?interface .
            ?externalSystem :L1_exposesInterface ?interface .
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]] = set()

    for result in bindings:
        internal_system_uri_binding = result.get("internalSystem")
        external_system_uri_binding = result.get("externalSystem")

        internal_system_uri = internal_system_uri_binding["value"] if internal_system_uri_binding else ""
        external_system_uri = external_system_uri_binding["value"] if external_system_uri_binding else ""

        results.add((STRIDE.SPOOFING, frozenset([(external_system_uri, internal_system_uri, internal_system_uri, CONTROL.CLIENT_AUTHENTICATION)])))
        results.add((STRIDE.INFORMATION_DISCLOSURE, frozenset([(external_system_uri, internal_system_uri, internal_system_uri, CONTROL.TRAFFIC_ENCRYPTION)])))

    return results

def RenderResults(results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]]) -> None:
    for result in results:
        print(f"⚠️  Threat: {result[0].value}")
        for entry in result[1]:
            print(f"    Attacker node: {entry[0]}")
            print(f"    Vulnerable node: {entry[1]}")
            print(f"    Mitigating entity: {entry[2]}")
            print(f"    Mitigating control: {entry[3].value}")


def L1_ThreatModeler() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]]:
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL]]]] = set()
    results.update(ExternalActorInternalSystem())
    results.update(InternalSystemExternalSystem())
    RenderResults(results)
    return results
