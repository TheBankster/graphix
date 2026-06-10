from collections import defaultdict
from graphdb import GetBindings
from stride import STRIDE
from controls import CONTROL
from typing import Set, Tuple, FrozenSet, Iterable

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
def ExternalActorInternalSystem() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]:
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?actor ?interface ?system ?hasClientAuth ?hasRateLimit ?hasAccessControl ?hasTransitEnc
        WHERE {
            # Core topology traversal
            ?actor a :L1_Actor .
            ?interface a :L1_Interface .
            ?system a :L1_InternalSystem .
            
            ?actor :L1_invokesInterface ?interface .
            ?system :L1_exposesInterface ?interface .

            # Check interface for endpoint controls
            OPTIONAL { 
                ?interface :CTL_RequiresControls :CTL_ClientAuthentication . 
                BIND(true AS ?hasClientAuth) 
            }
            OPTIONAL { 
                ?interface :CTL_RequiresControls :CTL_RateLimiting . 
                BIND(true AS ?hasRateLimit) 
            }
            OPTIONAL { 
                ?interface :CTL_RequiresControls :CTL_DataInTransitEncryption . 
                BIND(true AS ?hasTransitEnc) 
            }

            # Check internal system for logic/authorization controls
            OPTIONAL { 
                ?system :CTL_RequiresControls :CTL_AccessControl . 
                BIND(true AS ?hasAccessControl) 
            }
        }"""
    bindings = GetBindings(query)
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]] = set()

    for result in bindings:
        actor_uri = result.get("actor", {}).get("value", "")
        interface_uri = result.get("interface", {}).get("value", "")
        system_uri = result.get("system", {}).get("value", "")

        # Spoofing -> Mitigated by Client Authentication at the Interface
        results.add((
            STRIDE.SPOOFING, 
            frozenset([(actor_uri, system_uri, interface_uri, CONTROL.CLIENT_AUTHENTICATION, "hasClientAuth" in result)])
        ))

        # Denial of Service -> Mitigated by Rate Limiting at the Interface
        results.add((
            STRIDE.DENIAL_OF_SERVICE, 
            frozenset([(actor_uri, system_uri, interface_uri, CONTROL.RATE_LIMITING, "hasRateLimit" in result)])
        ))

        # Elevation of Privilege -> Mitigated by Access Control at the Internal System
        results.add((
            STRIDE.ELEVATION_OF_PRIVILEGE, 
            frozenset([(actor_uri, system_uri, system_uri, CONTROL.ACCESS_CONTROL, "hasAccessControl" in result)])
        ))

        # Information Disclosure -> Mitigated by Traffic Encryption at the Interface
        results.add((
            STRIDE.INFORMATION_DISCLOSURE, 
            frozenset([(actor_uri, system_uri, interface_uri, CONTROL.DATA_IN_TRANSIT_ENCRYPTION, "hasTransitEnc" in result)])
        ))

    return results

# Internal systems exposing external systems present these threats:
#   - Spoofing of the External Service, mitigated by Server Authentication by the Internal Service
#   - Information disclosure, mitigated by Traffic Encryption by the External Services' Interface
def InternalSystemExternalSystem() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]:
    # We select the systems and OPTIONALLY check if the specific mitigations exist
    query: str = """
        PREFIX : <http://thefirm.com/graphix#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?internalSystem ?externalSystem ?hasAuth ?hasEncryption
        WHERE {
            ?internalSystem a :L1_InternalSystem .
            ?interface a :L1_Interface .
            ?externalSystem a :L1_ExternalSystem .

            ?internalSystem :L1_invokesInterface ?interface .
            ?externalSystem :L1_exposesInterface ?interface .

            # Bind a variable if the mitigation exists, otherwise it remains unbound
            OPTIONAL { 
                ?internalSystem :CTL_RequiresControls :CTL_ServerAuthentication . 
                BIND(true AS ?hasAuth)
            }
            OPTIONAL { 
                ?internalSystem :CTL_RequiresControls :CTL_DataInTransitEncryption . 
                BIND(true AS ?hasEncryption)
            }
        }"""
        
    bindings = GetBindings(query)
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]] = set()

    for result in bindings:
        internal_system_uri = result.get("internalSystem", {}).get("value", "")
        external_system_uri = result.get("externalSystem", {}).get("value", "")

        # Spoofing mitigated by authentication
        results.add((
            STRIDE.SPOOFING, 
            frozenset([(external_system_uri, internal_system_uri, internal_system_uri, CONTROL.SERVER_AUTHENTICATION, "hasAuth" in result)])
        ))
        
        # Information disclosure mitigated by traffic encryption
        results.add((
            STRIDE.INFORMATION_DISCLOSURE, 
            frozenset([(external_system_uri, internal_system_uri, internal_system_uri, CONTROL.DATA_IN_TRANSIT_ENCRYPTION, "hasEncryption" in result)])
        ))

    return results

def RenderResults(results: Iterable[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]) -> None:
    # 1. Bucket the inner entries by their STRIDE threat type
    grouped_threats = defaultdict(list)
    for stride_type, entries_set in results:
        for entry in entries_set:
            grouped_threats[stride_type].append(entry)
            
    # 2. Iterate through the grouped categories in alphabetical order of the threat name
    for stride_type in sorted(grouped_threats.keys(), key=lambda x: x.value):
        entries = grouped_threats[stride_type]
        
        # Determine if the ENTIRE category is mitigated (True if ALL entries are true)
        all_mitigated = all(entry[4] for entry in entries)
        category_icon = "✅" if all_mitigated else "⚠️ "
        
        # Print the overarching threat category header ONCE
        print(f"\n{category_icon} Threat Category: {stride_type.value}")
        
        # Print each individual target link under this header
        for entry in entries:
            # Check the status of this specific link
            item_icon = "✅" if entry[4] else "⚠️ "
            
            print(f"    ---------------------------------------------")
            print(f"    Attacker node:     {entry[0]}")
            print(f"    Vulnerable node:   {entry[1]}")
            print(f"    Mitigating entity: {entry[2]}")
            print(f"    Mitigating control: {entry[3].value} {item_icon}")

def L1_ThreatModeler() -> Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]]:
    results: Set[Tuple[STRIDE, FrozenSet[Tuple[str, str, str, CONTROL, bool]]]] = set()
    
    # Accumulate all threats from different architectural bounds
    results.update(ExternalActorInternalSystem())
    results.update(InternalSystemExternalSystem())
    
    # Sort the results by the first element of the tuple (STRIDE enum value)
    # This groups all SPOOFING together, all DENIAL_OF_SERVICE together, etc.
    grouped_results = sorted(results, key=lambda x: x[0].value)
    
    # Pass the ordered list to the renderer so they print out cleanly grouped
    RenderResults(grouped_results)
    
    return results
