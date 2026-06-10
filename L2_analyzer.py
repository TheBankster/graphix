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

# All exposed L2 Interfaces must be invoked by at least one Container
def MissingInterfaceInvocations() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?l2_interface ?label
        WHERE {
            ?l2_interface a :L2_Interface .
            FILTER NOT EXISTS { ?caller :L2_invokesInterface ?l2_interface . }
            OPTIONAL { ?l2_interface rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()
   
    for result in bindings:
        interface_binding = result.get("l2_interface")
        interface_uri = interface_binding["value"] if interface_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((interface_uri, label))

    return results

# All Trust Boundaries must correspond to an Internal System Perimeter
def UnlinkedTrustBoundaries() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?trustBoundary ?label
        WHERE {
            ?trustBoundary a :L2_TrustBoundary .
            ?internalSystemPerimeter a :L1_InternalSystemPerimeter .
            FILTER NOT EXISTS { ?trustBoundary :L2_trustBoundary_to_L1 ?L1_InternalSystemPerimeter . }
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
            ?internalSystem a :L1_InternalSystem .
            FILTER NOT EXISTS { ?container :L2_container_to_L1 ?internalSystem . }
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

# All L2 interfaces must link to an L1 interface unless exposed and called within the same L1 Software System
def UnlinkedInterfaces() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?l2_interface ?label
        WHERE {
            ?l2_interface a :L2_Interface .
            # Condition 1: The L2 Interface must be missing its L1 Interface mapping
            FILTER NOT EXISTS {
                ?l1_interface a :L1_Interface .
                ?l2_interface :L2_Interface_to_L1 ?l1_interface . }
            # Condition 2: EXCLUDE if it's an internal call within the same L1 Software System
            FILTER NOT EXISTS {
                ?caller a :L2_Container .
                ?callee a :L2_Container .
                ?internalSystem a :L1_InternalSystem .
                
                ?caller :L2_invokesInterface ?l2_interface .
                ?callee :L2_exposesInterface ?l2_interface .
                
                # Both containers map back to the same L1 System
                ?caller :L2_container_to_L1 ?internalSystem .
                ?callee :L2_container_to_L1 ?internalSystem .
            }
            OPTIONAL { ?l2_interface rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()

    for result in bindings:
        interface_binding = result.get("l2_interface")
        interface_uri = interface_binding["value"] if interface_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((interface_uri, label))
        
    return results

# All L1 interfaces must have at least one L2 interface link to them
def UnutilizedInterfaces() -> Set[Tuple[str,str]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?l1_interface ?label
        WHERE {
            ?l1_interface a :L1_Interface .
            FILTER NOT EXISTS { 
                    ?l2_interface a :L2_Interface .
                    ?l2_interface :L2_Interface_to_L1 ?l1_interface . }
            OPTIONAL { ?l1_interface rdfs:label ?label . }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[str,str]] = set()

    for result in bindings:
        interface_binding = result.get("l1_interface")
        interface_uri = interface_binding["value"] if interface_binding else ""
        
        label_binding = result.get("label")
        label = label_binding["value"] if label_binding else ""        

        results.add((interface_uri, label))
        
    return results

def L2_SemanticAnalyzer() -> bool:
    result: bool = True
    containersMissingTrustBoundary = ContainersMissingTrustBoundary()
    missingInterfaceInvocations = MissingInterfaceInvocations()
    unlinkedTrustBoundaries = UnlinkedTrustBoundaries()
    unlinkedContainers = UnlinkedContainers()
    unlinkedInterfaces = UnlinkedInterfaces()
    unutilizedInterfaces = UnutilizedInterfaces()

    print("📐 Running L2 Semantic Analyzer...")

    if containersMissingTrustBoundary:
        result = False
        print("🛑 The following Containers are not inside a Trust Boundary:")
        for container in containersMissingTrustBoundary:
            print(f"  - {container}")

    if missingInterfaceInvocations:
        result = False
        print("🛑 The following Interface are not invoked by any Container:")
        for interface in missingInterfaceInvocations:
            print(f"  - {interface}")

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

    if unlinkedInterfaces:
        result = False
        print("🛑 The following L2 Interfaces are not linked to an L1 Interface:")
        for interface in unlinkedInterfaces:
            print(f"  - {interface}")

    if unutilizedInterfaces:
        result = False
        print("🛑 The following L1 Interfaces are not linked to by any L2 Interface:")
        for interface in unutilizedInterfaces:
            print(f"  - {interface}")

    if result:
        print("✅ L2 Semantic Check succeeded")

    return result