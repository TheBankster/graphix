from typing import Any, cast, Dict
from graphdb import GraphQueryClient
from SPARQLWrapper import JSON

def GetBindings(query: str) -> Any:
    client = GraphQueryClient()
    client.setQuery(query)
    client.setReturnFormat(JSON)
    raw_results = client.query().convert()
    results = cast(Dict[str, Any], raw_results)
    bindings = results["results"]["bindings"]
    return bindings

# All Internal Systems must be inside a Trust Boundary
def MissingTrustBoundaries() -> list[str]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?system ?label
        WHERE {
        ?system a :L1_InternalSystem .
        FILTER NOT EXISTS { ?system :L1_insideBoundary ?boundary . }
        OPTIONAL { ?system rdfs:label ?label }
        }"""
    bindings = GetBindings(query)
    results: list[str] = []
    
    for result in bindings:
        label = result.get("label", {}).get("value")
        if label:
            results.append(label)
    return results

# All Software Systems must expose an Interface
def MissingInterfaces() -> list[str]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?system ?label
        WHERE {
        ?system a :L1_SoftwareSystem .
        FILTER NOT EXISTS { ?system :L1_exposesInterface ?interface . }
        OPTIONAL { ?system rdfs:label ?label }
        }"""
    bindings = GetBindings(query)
    results: list[str] = []

    for result in bindings:
        label = result.get("label", {}).get("value")
        if label:
            results.append(label)

    return results

# All exposed Interfaces must be invoked by at least one Software System
def MissingInvocations() -> list[str]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?interface ?label
        WHERE {
        ?interface a :L1_Interface .
        FILTER NOT EXISTS { ?interface :L1_invokedBy ?system . }
        OPTIONAL { ?interface rdfs:label ?label }
        }"""
    bindings = GetBindings(query)
    results: list[str] = []
   
    for result in bindings:
        label = result.get("label", {}).get("value")
        if label:
            results.append(label)

    return results

def L1_SemanticAnalyzer() -> bool:
    result: bool = True
    missingTrustBoundaries = MissingTrustBoundaries()
    missingInterfaces = MissingInterfaces()
    missingInvocations = MissingInvocations()

    if missingInterfaces:
        result = False
        print(f"🛑 The following Software Systems are not exposing an Interface:")
        for interface in missingInterfaces:
            print(f"  - {interface}")

    if missingTrustBoundaries:
        result = False
        print(f"🛑 The following Internal Systems are not inside a Trust Boundary:")
        for system in missingTrustBoundaries:
            print(f"  - {system}")

    if missingInvocations:
        result = False
        print(f"🛑 The following Interfaces are not invoked by any Software System:")
        for interface in missingInvocations:
            print(f"  - {interface}")

    return result

def L2_Analyzer():
    pass

def L3_Analyzer():
    pass