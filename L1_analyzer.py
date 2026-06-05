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