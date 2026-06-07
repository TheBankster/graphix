from graphdb import GetBindings
from stride import STRIDE
from typing import Set, Tuple

### L1 Threat Modeling Rules ###

# External actors invoking internal systems present a spoofing and DoS threats
# Each Tuple returns:
#   - STRIDE threat (Spoofing or DoS)
#   - Tuple of Actor/Interface:
#       - Actor URI
#       - Actor Label
#       - Interface URI
#       - Interface Label
def ExternalActorInternalSystem() -> Set[Tuple[STRIDE, Tuple[str, str, str, str]]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?actor ?actorLabel ?interface ?interfaceLabel
        WHERE {
            ?actor a :L1_Actor .
            ?interface a :L1_Interface .
            ?system a :L1_InternalSystem .
            ?actor :L1_invokesInterface ?interface .
            ?system :L1_exposesInterface ?interface .
            OPTIONAL { ?actor rdfs:label ?actorLabel . }
            OPTIONAL { ?interface rdfs:label ?interfaceLabel . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[STRIDE, Tuple[str, str, str, str]]] = set()

    for result in bindings:
        actor_uri_binding = result.get("actor")
        actor_label_binding = result.get("actorLabel")
        interface_uri_binding = result.get("interface")
        interface_label_binding = result.get("interfaceLabel")

        actor_uri = actor_uri_binding["value"] if actor_uri_binding else ""
        actor_label = actor_label_binding["value"] if actor_label_binding else ""
        interface_uri = interface_uri_binding["value"] if interface_uri_binding else ""
        interface_label = interface_label_binding["value"] if interface_label_binding else ""

        results.add((STRIDE.SPOOFING, (actor_uri, actor_label, interface_uri, interface_label)))
        results.add((STRIDE.DENIAL_OF_SERVICE, (actor_uri, actor_label, interface_uri, interface_label)))

    return results

def RenderResults(results: Set[Tuple[STRIDE, Tuple[str, str, str, str]]]) -> None:
    for result in results:
        print(f"⚠️  Threat: {result[0].value}")
        print(f"    {result[1][0]} --> {result[1][2]}")

def L1_ThreatModeler() -> Set[Tuple[STRIDE, Tuple[str, str, str, str]]]:
    results: Set[Tuple[STRIDE, Tuple[str, str, str, str]]] = set()
    results.update(ExternalActorInternalSystem())
    RenderResults(results)
    return results
