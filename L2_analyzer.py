from graphdb import GetBindings
from typing import Set, Tuple

### L2 Semantic Analyizer Rules ###

# All functions in this section return a set of tuples where the first element
# is the URI of the offending node and the second element is its human-readable label

# All Containers must be inside a Trust Boundary
def ContainersMissingTrustBoundary() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?container ?label
        WHERE {
            ?container a :L2_Container .
            FILTER NOT EXISTS { ?container :L2_insideTrustBoundary ?trustBoundary . }
            OPTIONAL { ?container rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()
    
    for result in bindings:
        container_binding = result.get("container")
        container_uri = container_binding["value"] if container_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((container_uri, label))
        
    return results

# All exposed API must be invoked by at least one Container
def MissingAPIInvocations() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?API ?label
        WHERE {
            ?API a :L2_API .
            FILTER NOT EXISTS { ?caller :L2_invokesAPI ?API . }
            OPTIONAL { ?API rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()
   
    for result in bindings:
        API_binding = result.get("API")
        API_uri = API_binding["value"] if API_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((API_uri, label))

    return results

# All Containers must be inside a Trust Boundary
def UnlinkedTrustBoundaries() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?trustBoundary ?label
        WHERE {
            ?trustBoundary a :L2_TrustBoundary .
            FILTER NOT EXISTS { ?trustBoundary :L2_trustBoundary_to_L1 ?interface . }
            OPTIONAL { ?trustBoundary rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()
    
    for result in bindings:
        trustBoundary_binding = result.get("trustBoundary")
        trustBoundary_uri = trustBoundary_binding["value"] if trustBoundary_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((trustBoundary_uri, label))
        
    return results

# All Containers must be linked to an Internal System
def UnlinkedContainers() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?container ?label
        WHERE {
            ?container a :L2_Container .
            FILTER NOT EXISTS { ?container :L2_container_to_L1 ?interalSystem . }
            OPTIONAL { ?container rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()

    for result in bindings:
        container_binding = result.get("container")
        container_uri = container_binding["value"] if container_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((container_uri, label))
        
    return results

# All API must be linked to an Interface
def UnlinkedAPI() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?API ?label
        WHERE {
            ?API a :L2_API .
            FILTER NOT EXISTS { ?API :L2_API_to_L1 ?interface . }
            OPTIONAL { ?API rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()

    for result in bindings:
        API_binding = result.get("API")
        API_uri = API_binding["value"] if API_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((API_uri, label))
        
    return results

def L2_SemanticAnalyzer() -> bool:
    result: bool = True
    containersMissingTrustBoundary = ContainersMissingTrustBoundary()
    missingAPIInvocations = MissingAPIInvocations()
    unlinkedTrustBoundaries = UnlinkedTrustBoundaries()
    unlinkedContainers = UnlinkedContainers()
    unlinkedAPI = UnlinkedAPI()

    print("📐 Running L2 Semantic Analyzer...")

    if containersMissingTrustBoundary:
        result = False
        print("🛑 The following Containers are not inside a Trust Boundary:")
        for container in containersMissingTrustBoundary:
            print(f"  - {container}")

    if missingAPIInvocations:
        result = False
        print("🛑 The following API are not invoked by any Container:")
        for API in missingAPIInvocations:
            print(f"  - {API}")

    if unlinkedTrustBoundaries:
        result = False
        print("🛑 The following Trust Boundaries are not linked to a System Perimeter:")
        for trustBoundary in unlinkedTrustBoundaries:
            print(f"  - {trustBoundary}")

    if unlinkedContainers:
        result = False
        print("🛑 The following Containers are not linked to an Internal System:")
        for container in unlinkedContainers:
            print(f"  - {container}")

    if unlinkedAPI:
        result = False
        print("🛑 The following API are not linked to an Interface:")
        for API in unlinkedAPI:
            print(f"  - {API}")

    if result:
        print("🎈 L2 Semantic Check succeeded")

    return result