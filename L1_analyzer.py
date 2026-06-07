from graphdb import GetBindings
from typing import Set, Tuple

### L1 Semantic Analyizer Rules ###

# All Internal Systems must be inside a Trust Boundary
# The function returns a set of tuples where the first element is the URI of the offending node
# and the second element is its human-readable label
def MissingTrustBoundaries() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?system ?label
        WHERE {
            ?system a :L1_InternalSystem .
            FILTER NOT EXISTS { ?system :L1_insideBoundary ?boundary . }
            OPTIONAL { ?system rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()
    
    for result in bindings:
        system_binding = result.get("system")
        system_uri = system_binding["value"] if system_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((system_uri, label))
        
    return results

# All Software Systems must expose an Interface
# The function returns a set of tuples where the first element is the URI of the offending node
# and the second element is its human-readable label
def MissingInterfaces() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?system ?label
        WHERE {
            ?system a :L1_SoftwareSystem .
            FILTER NOT EXISTS { ?system :L1_exposesInterface ?interface . }
            OPTIONAL { ?system rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()

    for result in bindings:
        system_binding = result.get("system")
        system_uri = system_binding["value"] if system_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((system_uri, label))

    return results

# All exposed Interfaces must be invoked by at least one Software System
def MissingInvocations() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?interface ?label
        WHERE {
            ?interface a :L1_Interface .
            FILTER NOT EXISTS { ?system :L1_invokesInterface ?interface . }
            OPTIONAL { ?interface rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()
   
    for result in bindings:
        interface_binding = result.get("interface")
        interface_uri = interface_binding["value"] if interface_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((interface_uri, label))

    return results

def L1_SemanticAnalyzer() -> bool:
    result: bool = True
    missingTrustBoundaries = MissingTrustBoundaries()
    missingInterfaces = MissingInterfaces()
    missingInvocations = MissingInvocations()

    print("📐 Running L1 Semantic Analyzer...")

    if missingInterfaces:
        result = False
        print("🛑 The following Software Systems are not exposing an Interface:")
        for interface in missingInterfaces:
            print(f"  - {interface}")

    if missingTrustBoundaries:
        result = False
        print("🛑 The following Internal Systems are not inside a Trust Boundary:")
        for system in missingTrustBoundaries:
            print(f"  - {system}")

    if missingInvocations:
        result = False
        print("🛑 The following Interfaces are not invoked by any Software System:")
        for interface in missingInvocations:
            print(f"  - {interface}")

    if result:
        print("🎈 L1 Semantic Check succeeded")

    return result

def L2_Analyzer():
    pass

def L3_Analyzer():
    pass